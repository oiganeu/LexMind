"""Unit tests for the Artifact Management System (Task 15).

Covers:
  - ArtifactType enum and pipeline ordering
  - ArtifactStatus states and transitions
  - Artifact aggregate lifecycle + versioning
  - DependencyGraph (DAG operations, cycle detection, topological sort)
  - LineageTracker provenance chains
  - ArtifactManifest validation
  - ArtifactManager orchestration
  - Artifact events
  - Artifact exceptions
  - No infrastructure dependencies
"""

from unittest.mock import MagicMock

import pytest

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_dependency import ArtifactDependency, DependencyGraph
from lexmind.artifacts.artifact_events import (
    ArtifactArchived,
    ArtifactCreated,
    ArtifactDeleted,
    ArtifactSuperseded,
    ArtifactValidated,
)
from lexmind.artifacts.artifact_exceptions import (
    ArtifactAlreadyExistsError,
    ArtifactChecksumError,
    ArtifactDependencyError,
    ArtifactError,
    ArtifactNotFoundError,
    ArtifactStateError,
    ArtifactValidationError,
    ArtifactVersionError,
)
from lexmind.artifacts.artifact_lineage import LineageTracker
from lexmind.artifacts.artifact_manager import ArtifactManager
from lexmind.artifacts.artifact_manifest import (
    ArtifactManifest,
    ArtifactManifestValidator,
)
from lexmind.artifacts.artifact_metadata import ArtifactMetadata
from lexmind.artifacts.artifact_state import (
    VALID_ARTIFACT_TRANSITIONS,
    ArtifactStatus,
    can_transition_artifact,
)
from lexmind.artifacts.artifact_types import PIPELINE_ORDER, ArtifactType

# ---------------------------------------------------------------------------
# ArtifactType
# ---------------------------------------------------------------------------

class TestArtifactType:
    """Tests for ArtifactType enum."""

    def test_all_types_defined(self) -> None:
        assert len(ArtifactType) == 19

    def test_pipeline_order_subset(self) -> None:
        for at in PIPELINE_ORDER:
            assert isinstance(at, ArtifactType)

    def test_pipeline_order_starts_with_original(self) -> None:
        assert PIPELINE_ORDER[0] == ArtifactType.ORIGINAL_DOCUMENT

    def test_type_values_are_strings(self) -> None:
        for at in ArtifactType:
            assert isinstance(at.value, str)


# ---------------------------------------------------------------------------
# ArtifactStatus and transitions
# ---------------------------------------------------------------------------

class TestArtifactStatus:
    """Tests for ArtifactStatus enum and transition graph."""

    def test_all_states(self) -> None:
        expected = {"registered", "available", "invalid", "superseded", "archived", "deleted"}
        assert {s.value for s in ArtifactStatus} == expected

    def test_registered_to_available(self) -> None:
        assert can_transition_artifact(ArtifactStatus.REGISTERED, ArtifactStatus.AVAILABLE)

    def test_registered_to_invalid(self) -> None:
        assert can_transition_artifact(ArtifactStatus.REGISTERED, ArtifactStatus.INVALID)

    def test_available_to_superseded(self) -> None:
        assert can_transition_artifact(ArtifactStatus.AVAILABLE, ArtifactStatus.SUPERSEDED)

    def test_available_to_archived(self) -> None:
        assert can_transition_artifact(ArtifactStatus.AVAILABLE, ArtifactStatus.ARCHIVED)

    def test_available_to_deleted(self) -> None:
        assert can_transition_artifact(ArtifactStatus.AVAILABLE, ArtifactStatus.DELETED)

    def test_invalid_to_deleted(self) -> None:
        assert can_transition_artifact(ArtifactStatus.INVALID, ArtifactStatus.DELETED)

    def test_superseded_to_archived(self) -> None:
        assert can_transition_artifact(ArtifactStatus.SUPERSEDED, ArtifactStatus.ARCHIVED)

    def test_archived_to_deleted(self) -> None:
        assert can_transition_artifact(ArtifactStatus.ARCHIVED, ArtifactStatus.DELETED)

    def test_deleted_is_terminal(self) -> None:
        assert VALID_ARTIFACT_TRANSITIONS[ArtifactStatus.DELETED] == frozenset()

    def test_invalid_transitions(self) -> None:
        invalid_pairs = [
            (ArtifactStatus.REGISTERED, ArtifactStatus.SUPERSEDED),
            (ArtifactStatus.REGISTERED, ArtifactStatus.ARCHIVED),
            (ArtifactStatus.REGISTERED, ArtifactStatus.DELETED),
            (ArtifactStatus.AVAILABLE, ArtifactStatus.REGISTERED),
            (ArtifactStatus.ARCHIVED, ArtifactStatus.AVAILABLE),
        ]
        for src, dst in invalid_pairs:
            assert not can_transition_artifact(src, dst), f"{src}->{dst} should be invalid"


# ---------------------------------------------------------------------------
# Artifact aggregate
# ---------------------------------------------------------------------------

class TestArtifact:
    """Tests for Artifact aggregate root."""

    def _make(self, **kwargs: object) -> Artifact:
        defaults: dict[str, object] = {
            "id": "art-001",
            "workspace_id": "ws-001",
            "artifact_type": ArtifactType.OCR_TEXT,
            "checksum": "abc123",
        }
        defaults.update(kwargs)
        return Artifact(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        art = self._make()
        assert art.id == "art-001"
        assert art.status == ArtifactStatus.REGISTERED
        assert art.current_version == 1

    def test_missing_id_raises(self) -> None:
        with pytest.raises(ArtifactValidationError):
            Artifact(workspace_id="ws-1", artifact_type=ArtifactType.LOG, checksum="x")

    def test_missing_workspace_raises(self) -> None:
        with pytest.raises(ArtifactValidationError):
            Artifact(id="a-1", artifact_type=ArtifactType.LOG, checksum="x")

    def test_lifecycle_happy_path(self) -> None:
        art = self._make()
        art.mark_available()
        assert art.status == ArtifactStatus.AVAILABLE
        art.archive()
        assert art.status == ArtifactStatus.ARCHIVED
        art.delete()
        assert art.status == ArtifactStatus.DELETED

    def test_invalid_transition_raises(self) -> None:
        art = self._make()
        with pytest.raises(ArtifactStateError):
            art.supersede()

    def test_new_version(self) -> None:
        art = self._make()
        art.mark_available()
        ver = art.create_new_version(checksum="def456", notes="re-ocr")
        assert ver.version_number == 2
        assert ver.checksum == "def456"
        assert art.current_version == 2
        assert art.checksum == "def456"

    def test_version_history(self) -> None:
        art = self._make()
        art.create_new_version(checksum="v2")
        art.create_new_version(checksum="v3")
        history = art.version_history()
        assert len(history) == 2
        assert history[0].version_number == 2
        assert history[1].version_number == 3

    def test_latest_version(self) -> None:
        art = self._make()
        assert art.latest_version() is None
        art.create_new_version(checksum="v2")
        latest = art.latest_version()
        assert latest is not None
        assert latest.version_number == 2

    def test_cannot_version_deleted(self) -> None:
        art = self._make()
        art.delete()
        with pytest.raises(ArtifactStateError):
            art.create_new_version(checksum="x")

    def test_cannot_version_archived(self) -> None:
        art = self._make()
        art.mark_available()
        art.archive()
        with pytest.raises(ArtifactStateError):
            art.create_new_version(checksum="x")

    def test_validate_checksum(self) -> None:
        art = self._make(checksum="abc123")
        assert art.validate_checksum("abc123")
        assert not art.validate_checksum("wrong")

    def test_tags(self) -> None:
        art = self._make()
        art.add_tag("ocr")
        art.add_tag("v2")
        assert "ocr" in art.tags
        assert "v2" in art.tags
        art.add_tag("ocr")
        assert art.tags.count("ocr") == 1
        art.remove_tag("ocr")
        assert "ocr" not in art.tags

    def test_build_metadata(self) -> None:
        art = self._make(workspace_id="ws-x")
        meta = art.build_metadata()
        assert meta.workspace_id == "ws-x"
        assert meta.artifact_type == "ocr_text"

    def test_build_manifest(self) -> None:
        art = self._make()
        result = art.validate_manifest()
        assert result.is_valid


# ---------------------------------------------------------------------------
# DependencyGraph
# ---------------------------------------------------------------------------

class TestDependencyGraph:
    """Tests for DependencyGraph DAG operations."""

    def test_add_simple(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        assert "b" in g.children("a")
        assert "a" in g.parents("b")

    def test_self_dependency_raises(self) -> None:
        g = DependencyGraph()
        with pytest.raises(ValueError, match="Self-dependency"):
            g.add(ArtifactDependency(parent_id="a", child_id="a"))

    def test_cycle_detection(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        g.add(ArtifactDependency(parent_id="b", child_id="c"))
        with pytest.raises(ValueError, match="cycle"):
            g.add(ArtifactDependency(parent_id="c", child_id="a"))

    def test_roots(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        g.add(ArtifactDependency(parent_id="b", child_id="c"))
        assert g.roots() == frozenset({"a"})

    def test_leaves(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        g.add(ArtifactDependency(parent_id="b", child_id="c"))
        assert g.leaves() == frozenset({"c"})

    def test_topological_order(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        g.add(ArtifactDependency(parent_id="b", child_id="c"))
        order = g.topological_order()
        assert order.index("a") < order.index("b") < order.index("c")

    def test_remove(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="a", child_id="b"))
        g.remove("a")
        assert "b" not in g.children("a")
        assert "a" not in g.parents("b")

    def test_all_artifacts(self) -> None:
        g = DependencyGraph()
        g.add(ArtifactDependency(parent_id="x", child_id="y"))
        g.add(ArtifactDependency(parent_id="y", child_id="z"))
        assert g.all_artifacts() == frozenset({"x", "y", "z"})

    def test_empty_graph(self) -> None:
        g = DependencyGraph()
        assert g.roots() == frozenset()
        assert g.leaves() == frozenset()
        assert g.topological_order() == []


# ---------------------------------------------------------------------------
# LineageTracker
# ---------------------------------------------------------------------------

class TestLineageTracker:
    """Tests for LineageTracker provenance tracking."""

    def _build_linear_chain(self) -> LineageTracker:
        tracker = LineageTracker()
        for parent, child in [("a", "b"), ("b", "c"), ("c", "d")]:
            tracker.graph.add(ArtifactDependency(parent_id=parent, child_id=child))
        return tracker

    def test_ancestors(self) -> None:
        t = self._build_linear_chain()
        assert set(t.ancestors("d")) == {"a", "b", "c"}

    def test_descendants(self) -> None:
        t = self._build_linear_chain()
        assert set(t.descendants("a")) == {"b", "c", "d"}

    def test_full_chain(self) -> None:
        t = self._build_linear_chain()
        chain = t.full_chain("d")
        assert chain[0] == "a"
        assert chain[-1] == "d"

    def test_pipeline_stage(self) -> None:
        t = self._build_linear_chain()
        assert t.pipeline_stage("a") == 0
        assert t.pipeline_stage("d") >= 1


# ---------------------------------------------------------------------------
# ArtifactManifest
# ---------------------------------------------------------------------------

class TestArtifactManifest:
    """Tests for ArtifactManifest and ArtifactManifestValidator."""

    def test_valid_manifest(self) -> None:
        m = ArtifactManifest(
            artifact_id="a1",
            workspace_id="w1",
            artifact_type="ocr_text",
            checksum="abc",
        )
        result = ArtifactManifestValidator().validate(m)
        assert result.is_valid

    def test_missing_artifact_id(self) -> None:
        m = ArtifactManifest(workspace_id="w1", artifact_type="t", checksum="x")
        result = ArtifactManifestValidator().validate(m)
        assert not result.is_valid

    def test_missing_workspace_id(self) -> None:
        m = ArtifactManifest(artifact_id="a1", artifact_type="t", checksum="x")
        result = ArtifactManifestValidator().validate(m)
        assert not result.is_valid

    def test_missing_checksum(self) -> None:
        m = ArtifactManifest(artifact_id="a1", workspace_id="w1", artifact_type="t")
        result = ArtifactManifestValidator().validate(m)
        assert not result.is_valid

    def test_zero_version(self) -> None:
        m = ArtifactManifest(
            artifact_id="a1", workspace_id="w1",
            artifact_type="t", checksum="x", version=0,
        )
        result = ArtifactManifestValidator().validate(m)
        assert not result.is_valid

    def test_unsupported_schema_version(self) -> None:
        m = ArtifactManifest(
            artifact_id="a1", workspace_id="w1",
            artifact_type="t", checksum="x",
            schema_version="99.0",
        )
        result = ArtifactManifestValidator().validate(m)
        assert not result.is_valid


# ---------------------------------------------------------------------------
# ArtifactMetadata
# ---------------------------------------------------------------------------

class TestArtifactMetadata:
    """Tests for ArtifactMetadata value object."""

    def test_frozen(self) -> None:
        m = ArtifactMetadata(artifact_id="a1", workspace_id="w1")
        with pytest.raises(AttributeError):
            m.artifact_id = "x"  # type: ignore[misc]

    def test_defaults(self) -> None:
        m = ArtifactMetadata()
        assert m.version == 1
        assert m.tags == ()
        assert m.extra == {}


# ---------------------------------------------------------------------------
# ArtifactManager
# ---------------------------------------------------------------------------

class TestArtifactManager:
    """Tests for ArtifactManager orchestration."""

    def _make_manager(self) -> tuple[ArtifactManager, MagicMock]:
        registry = MagicMock()
        event_bus = MagicMock()
        registry.exists.return_value = False
        registry.find.return_value = None

        mgr = ArtifactManager(registry=registry, event_bus=event_bus)
        return mgr, event_bus

    def test_create_artifact(self) -> None:
        mgr, event_bus = self._make_manager()
        art = mgr.create_artifact(
            artifact_id="a1",
            workspace_id="w1",
            artifact_type=ArtifactType.OCR_TEXT,
            checksum="abc",
        )
        assert art.id == "a1"
        mgr._registry.register.assert_called_once()
        event_bus.publish.assert_called()

    def test_create_duplicate_raises(self) -> None:
        mgr, _ = self._make_manager()
        mgr._registry.exists.return_value = True
        with pytest.raises(ArtifactAlreadyExistsError):
            mgr.create_artifact(
                artifact_id="a1",
                workspace_id="w1",
                artifact_type=ArtifactType.LOG,
                checksum="x",
            )

    def test_validate_artifact(self) -> None:
        mgr, _ = self._make_manager()
        art = Artifact(id="a1", workspace_id="w1", checksum="abc")
        mgr._registry.find.return_value = art
        result = mgr.validate_artifact("a1", "abc")
        assert result is True
        assert art.status == ArtifactStatus.AVAILABLE

    def test_validate_checksum_mismatch(self) -> None:
        mgr, _ = self._make_manager()
        art = Artifact(id="a1", workspace_id="w1", checksum="abc")
        mgr._registry.find.return_value = art
        with pytest.raises(ArtifactChecksumError):
            mgr.validate_artifact("a1", "wrong")

    def test_supersede_artifact(self) -> None:
        mgr, _ = self._make_manager()
        art = Artifact(id="a1", workspace_id="w1", checksum="x")
        art.mark_available()
        mgr._registry.find.return_value = art
        mgr.supersede_artifact("a1")
        assert art.status == ArtifactStatus.SUPERSEDED

    def test_archive_artifact(self) -> None:
        mgr, _ = self._make_manager()
        art = Artifact(id="a1", workspace_id="w1", checksum="x")
        art.mark_available()
        mgr._registry.find.return_value = art
        mgr.archive_artifact("a1")
        assert art.status == ArtifactStatus.ARCHIVED

    def test_delete_artifact(self) -> None:
        mgr, _ = self._make_manager()
        art = Artifact(id="a1", workspace_id="w1", checksum="x")
        mgr._registry.find.return_value = art
        mgr.delete_artifact("a1")
        assert art.status == ArtifactStatus.DELETED

    def test_not_found_raises(self) -> None:
        mgr, _ = self._make_manager()
        mgr._registry.find.return_value = None
        with pytest.raises(ArtifactNotFoundError):
            mgr.validate_artifact("missing", "x")

    def test_add_dependency(self) -> None:
        mgr, _ = self._make_manager()
        a = Artifact(id="a1", workspace_id="w1", checksum="x")
        b = Artifact(id="b1", workspace_id="w1", checksum="y")

        def _find(aid: str) -> Artifact | None:
            return {"a1": a, "b1": b}.get(aid)

        mgr._registry.find.side_effect = _find
        mgr._registry.exists.return_value = True
        mgr.add_dependency("a1", "b1")
        assert "b1" in mgr._dependencies.children("a1")

    def test_lineage(self) -> None:
        mgr, _ = self._make_manager()
        arts = {}
        for aid in ["a", "b", "c"]:
            art = Artifact(id=aid, workspace_id="w1", checksum="x")
            arts[aid] = art

        def _find(aid: str) -> Artifact | None:
            return arts.get(aid)

        mgr._registry.find.side_effect = _find
        mgr._registry.exists.return_value = True
        mgr._dependencies.add(ArtifactDependency(parent_id="a", child_id="b"))
        mgr._dependencies.add(ArtifactDependency(parent_id="b", child_id="c"))
        chain = mgr.lineage("c")
        assert "a" in chain
        assert "c" in chain

    def test_list_by_type(self) -> None:
        mgr, _ = self._make_manager()
        mgr._registry.find_by_type.return_value = []
        result = mgr.list_by_type(ArtifactType.REPORT)
        assert result == []


# ---------------------------------------------------------------------------
# Artifact events
# ---------------------------------------------------------------------------

class TestArtifactEvents:
    """Tests for artifact lifecycle events."""

    def test_created(self) -> None:
        e = ArtifactCreated(aggregate_id="a1", artifact_type="ocr_text", producer="ocr")
        assert e.artifact_type == "ocr_text"

    def test_validated(self) -> None:
        e = ArtifactValidated(aggregate_id="a1", checksum_valid=True)
        assert e.checksum_valid is True

    def test_archived(self) -> None:
        e = ArtifactArchived(aggregate_id="a1")
        assert e.aggregate_id == "a1"

    def test_superseded(self) -> None:
        e = ArtifactSuperseded(aggregate_id="a1", superseded_by="a2")
        assert e.superseded_by == "a2"

    def test_deleted(self) -> None:
        e = ArtifactDeleted(aggregate_id="a1")
        assert e.aggregate_id == "a1"

    def test_events_are_frozen(self) -> None:
        e = ArtifactCreated(aggregate_id="a1")
        with pytest.raises(AttributeError):
            e.aggregate_id = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Artifact exceptions
# ---------------------------------------------------------------------------

class TestArtifactExceptions:
    """Tests for artifact exception hierarchy."""

    def test_base_is_lexmind_error(self) -> None:
        from lexmind.exceptions import LexMindError
        assert issubclass(ArtifactError, LexMindError)

    def test_not_found(self) -> None:
        e = ArtifactNotFoundError("a1")
        assert "a1" in str(e)

    def test_already_exists(self) -> None:
        e = ArtifactAlreadyExistsError("a1")
        assert "a1" in str(e)

    def test_validation_error(self) -> None:
        e = ArtifactValidationError("a1", reason="bad")
        assert "bad" in str(e)

    def test_checksum_error(self) -> None:
        e = ArtifactChecksumError("a1", expected="abc", actual="def")
        assert "abc" in str(e)
        assert "def" in str(e)

    def test_dependency_error(self) -> None:
        e = ArtifactDependencyError("a1", missing=("x", "y"))
        assert "x" in str(e)

    def test_version_error(self) -> None:
        e = ArtifactVersionError("a1", detail="nope")
        assert "nope" in str(e)

    def test_state_error(self) -> None:
        e = ArtifactStateError("a1", current_state="deleted", operation="version")
        assert "version" in str(e)


# ---------------------------------------------------------------------------
# No infrastructure dependencies
# ---------------------------------------------------------------------------

class TestNoInfrastructureDependencies:
    """Artifact system must not import SQL, ORM, or FastAPI."""

    def test_no_sql_imports(self) -> None:
        import inspect

        import lexmind.artifacts as pkg

        source = inspect.getsource(pkg)
        for mod in ["sqlite", "sqlalchemy", "psycopg", "asyncpg"]:
            assert mod not in source, f"Found forbidden import: {mod}"

    def test_no_fastapi_imports(self) -> None:
        import inspect

        import lexmind.artifacts as pkg

        source = inspect.getsource(pkg)
        assert "fastapi" not in source

    def test_all_classes_have_docstrings(self) -> None:
        import inspect

        import lexmind.artifacts as pkg

        public_classes = [
            obj for name, obj in inspect.getmembers(pkg)
            if inspect.isclass(obj)
            and not name.startswith("_")
            and obj.__module__.startswith("lexmind.artifacts")
        ]
        for cls in public_classes:
            assert cls.__doc__, f"{cls.__name__} is missing a docstring"
