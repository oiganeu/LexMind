"""Unit tests for the Workspace Engine (Task 14).

Covers:
  - WorkspaceStatus states and transitions
  - WorkspaceMetadata value object
  - WorkspaceManifest and ManifestValidator
  - Workspace aggregate lifecycle
  - SingleProcessLock
  - Workspace events
  - Workspace exceptions
  - WorkspaceManager orchestration
  - No infrastructure dependencies
"""

import threading
from unittest.mock import MagicMock

import pytest

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.workspace.workspace import (
    WORKSPACE_DIRECTORIES,
    Workspace,
)
from lexmind.workspace.workspace_context import (
    Configuration,
    EventBus,
    Logger,
    PluginManager,
    StorageProvider,
)
from lexmind.workspace.workspace_events import (
    WorkspaceArchived,
    WorkspaceClosed,
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceMigrated,
    WorkspaceOpened,
    WorkspaceValidationFailed,
)
from lexmind.workspace.workspace_exceptions import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptedError,
    WorkspaceError,
    WorkspaceLockError,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceNotOpenError,
    WorkspaceValidationError,
)
from lexmind.workspace.workspace_lock import SingleProcessLock, WorkspaceLock
from lexmind.workspace.workspace_manager import WorkspaceManager
from lexmind.workspace.workspace_manifest import (
    ManifestValidator,
    WorkspaceManifest,
)
from lexmind.workspace.workspace_metadata import WorkspaceMetadata
from lexmind.workspace.workspace_state import (
    VALID_TRANSITIONS,
    WorkspaceStatus,
    can_transition,
)

# ---------------------------------------------------------------------------
# WorkspaceStatus and transitions
# ---------------------------------------------------------------------------

class TestWorkspaceStatus:
    """Tests for WorkspaceStatus enum and transition graph."""

    def test_all_states_defined(self) -> None:
        expected = {
            "created", "open", "active", "read_only",
            "locked", "closed", "archived", "corrupted",
        }
        assert {s.value for s in WorkspaceStatus} == expected

    def test_created_to_open(self) -> None:
        assert can_transition(WorkspaceStatus.CREATED, WorkspaceStatus.OPEN)

    def test_open_to_active(self) -> None:
        assert can_transition(WorkspaceStatus.OPEN, WorkspaceStatus.ACTIVE)

    def test_open_to_read_only(self) -> None:
        assert can_transition(WorkspaceStatus.OPEN, WorkspaceStatus.READ_ONLY)

    def test_open_to_closed(self) -> None:
        assert can_transition(WorkspaceStatus.OPEN, WorkspaceStatus.CLOSED)

    def test_active_to_locked(self) -> None:
        assert can_transition(WorkspaceStatus.ACTIVE, WorkspaceStatus.LOCKED)

    def test_active_to_read_only(self) -> None:
        assert can_transition(WorkspaceStatus.ACTIVE, WorkspaceStatus.READ_ONLY)

    def test_active_to_closed(self) -> None:
        assert can_transition(WorkspaceStatus.ACTIVE, WorkspaceStatus.CLOSED)

    def test_read_only_to_active(self) -> None:
        assert can_transition(WorkspaceStatus.READ_ONLY, WorkspaceStatus.ACTIVE)

    def test_locked_to_active(self) -> None:
        assert can_transition(WorkspaceStatus.LOCKED, WorkspaceStatus.ACTIVE)

    def test_closed_to_archived(self) -> None:
        assert can_transition(WorkspaceStatus.CLOSED, WorkspaceStatus.ARCHIVED)

    def test_closed_to_open(self) -> None:
        assert can_transition(WorkspaceStatus.CLOSED, WorkspaceStatus.OPEN)

    def test_archived_to_open(self) -> None:
        assert can_transition(WorkspaceStatus.ARCHIVED, WorkspaceStatus.OPEN)

    def test_corrupted_is_terminal(self) -> None:
        assert VALID_TRANSITIONS[WorkspaceStatus.CORRUPTED] == frozenset()

    def test_invalid_transitions(self) -> None:
        invalid_pairs = [
            (WorkspaceStatus.CREATED, WorkspaceStatus.ACTIVE),
            (WorkspaceStatus.CREATED, WorkspaceStatus.CLOSED),
            (WorkspaceStatus.OPEN, WorkspaceStatus.ARCHIVED),
            (WorkspaceStatus.ACTIVE, WorkspaceStatus.OPEN),
            (WorkspaceStatus.LOCKED, WorkspaceStatus.CLOSED),
            (WorkspaceStatus.ARCHIVED, WorkspaceStatus.ACTIVE),
        ]
        for src, dst in invalid_pairs:
            assert not can_transition(src, dst), f"{src}->{dst} should be invalid"

    def test_all_states_have_transitions_entry(self) -> None:
        for state in WorkspaceStatus:
            assert state in VALID_TRANSITIONS


# ---------------------------------------------------------------------------
# WorkspaceMetadata
# ---------------------------------------------------------------------------

class TestWorkspaceMetadata:
    """Tests for WorkspaceMetadata value object."""

    def test_creation_defaults(self) -> None:
        meta = WorkspaceMetadata(workspace_id="w1", name="Test")
        assert meta.workspace_id == "w1"
        assert meta.name == "Test"
        assert meta.version == "1.0.0"
        assert meta.language == "ro"
        assert meta.status == "created"
        assert meta.tags == ()

    def test_frozen(self) -> None:
        meta = WorkspaceMetadata(workspace_id="w1", name="Test")
        with pytest.raises(AttributeError):
            meta.name = "Other"  # type: ignore[misc]

    def test_equality(self) -> None:
        from datetime import UTC, datetime

        ts = datetime(2025, 1, 1, tzinfo=UTC)
        a = WorkspaceMetadata(
            workspace_id="w1", name="A",
            created_at=ts, updated_at=ts,
        )
        b = WorkspaceMetadata(
            workspace_id="w1", name="A",
            created_at=ts, updated_at=ts,
        )
        assert a == b

    def test_inequality(self) -> None:
        from datetime import UTC, datetime

        ts = datetime(2025, 1, 1, tzinfo=UTC)
        a = WorkspaceMetadata(
            workspace_id="w1", name="A",
            created_at=ts, updated_at=ts,
        )
        b = WorkspaceMetadata(
            workspace_id="w2", name="A",
            created_at=ts, updated_at=ts,
        )
        assert a != b

    def test_tags_immutable(self) -> None:
        meta = WorkspaceMetadata(workspace_id="w1", name="T", tags=("a", "b"))
        assert meta.tags == ("a", "b")


# ---------------------------------------------------------------------------
# WorkspaceManifest and ManifestValidator
# ---------------------------------------------------------------------------

class TestWorkspaceManifest:
    """Tests for WorkspaceManifest and ManifestValidator."""

    def _valid_manifest(self) -> WorkspaceManifest:
        return WorkspaceManifest(
            workspace_id="w-001",
            name="My Workspace",
        )

    def test_valid_manifest_passes(self) -> None:
        result = ManifestValidator().validate(self._valid_manifest())
        assert result.is_valid
        assert result.errors == ()

    def test_missing_workspace_id(self) -> None:
        m = WorkspaceManifest(name="Test")
        result = ManifestValidator().validate(m)
        assert not result.is_valid
        assert any("workspace_id" in e for e in result.errors)

    def test_missing_name(self) -> None:
        m = WorkspaceManifest(workspace_id="w1")
        result = ManifestValidator().validate(m)
        assert not result.is_valid
        assert any("name" in e for e in result.errors)

    def test_unsupported_version(self) -> None:
        m = WorkspaceManifest(workspace_id="w1", name="T", version="99.0")
        result = ManifestValidator().validate(m)
        assert not result.is_valid
        assert any("version" in e for e in result.errors)

    def test_empty_language_warns(self) -> None:
        m = WorkspaceManifest(workspace_id="w1", name="T", language="")
        result = ManifestValidator().validate(m)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_manifest_frozen(self) -> None:
        m = self._valid_manifest()
        with pytest.raises(AttributeError):
            m.name = "Other"  # type: ignore[misc]

    def test_manifest_defaults(self) -> None:
        m = WorkspaceManifest()
        assert m.version == "1.0.0"
        assert m.language == "ro"
        assert m.storage_version == "1"
        assert m.default_plugins == ()
        assert m.enabled_features == ()


# ---------------------------------------------------------------------------
# Workspace aggregate
# ---------------------------------------------------------------------------

class TestWorkspace:
    """Tests for Workspace aggregate lifecycle."""

    def _make_ws(self, **kwargs: object) -> Workspace:
        defaults = {"id": "ws-001", "name": "Test Workspace"}
        defaults.update(kwargs)
        return Workspace(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        ws = self._make_ws()
        assert ws.id == "ws-001"
        assert ws.status == WorkspaceStatus.CREATED
        assert ws.name == "Test Workspace"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Workspace(id="x", name="")

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Workspace(id="x", name="   ")

    def test_workspace_id_property(self) -> None:
        ws = self._make_ws(id="ws-abc")
        assert ws.workspace_id.value == "ws-abc"

    def test_lifecycle_happy_path(self) -> None:
        ws = self._make_ws()
        ws.open()
        assert ws.status == WorkspaceStatus.OPEN
        ws.activate()
        assert ws.status == WorkspaceStatus.ACTIVE
        ws.close()
        assert ws.status == WorkspaceStatus.CLOSED

    def test_invalid_transition_raises(self) -> None:
        ws = self._make_ws()
        with pytest.raises(WorkspaceValidationError):
            ws.activate()

    def test_lock_unlock(self) -> None:
        ws = self._make_ws()
        ws.open()
        ws.activate()
        ws.lock()
        assert ws.status == WorkspaceStatus.LOCKED
        ws.unlock()
        assert ws.status == WorkspaceStatus.ACTIVE

    def test_read_only(self) -> None:
        ws = self._make_ws()
        ws.open()
        ws.set_read_only()
        assert ws.status == WorkspaceStatus.READ_ONLY
        ws.activate()
        assert ws.status == WorkspaceStatus.ACTIVE

    def test_archive(self) -> None:
        ws = self._make_ws()
        ws.open()
        ws.close()
        ws.archive()
        assert ws.status == WorkspaceStatus.ARCHIVED

    def test_reopen_from_closed(self) -> None:
        ws = self._make_ws()
        ws.open()
        ws.close()
        ws.reopen()
        assert ws.status == WorkspaceStatus.OPEN

    def test_reopen_from_archived(self) -> None:
        ws = self._make_ws()
        ws.open()
        ws.close()
        ws.archive()
        ws.reopen()
        assert ws.status == WorkspaceStatus.OPEN

    def test_mark_corrupted(self) -> None:
        ws = self._make_ws()
        ws.mark_corrupted()
        assert ws.status == WorkspaceStatus.CORRUPTED

    def test_corrupted_cannot_transition(self) -> None:
        ws = self._make_ws()
        ws.mark_corrupted()
        with pytest.raises(WorkspaceValidationError):
            ws.open()

    def test_validate_manifest_none(self) -> None:
        ws = self._make_ws()
        result = ws.validate_manifest()
        assert not result.is_valid

    def test_validate_manifest_valid(self) -> None:
        ws = self._make_ws()
        m = WorkspaceManifest(workspace_id="ws-001", name="Test")
        result = ws.validate_manifest(m)
        assert result.is_valid

    def test_validate_directories_all_present(self) -> None:
        ws = self._make_ws()
        dirs = frozenset(WORKSPACE_DIRECTORIES)
        missing = ws.validate_directories(dirs)
        assert missing == ()

    def test_validate_directories_missing(self) -> None:
        ws = self._make_ws()
        missing = ws.validate_directories(frozenset({"metadata", "original"}))
        assert "processed" in missing
        assert "cache" in missing

    def test_build_metadata(self) -> None:
        ws = self._make_ws(id="ws-x", name="Meta Test")
        meta = ws.build_metadata()
        assert meta.workspace_id == "ws-x"
        assert meta.name == "Meta Test"
        assert meta.status == "created"

    def test_increment_document_count(self) -> None:
        ws = self._make_ws()
        assert ws.document_count == 0
        ws.increment_document_count()
        ws.increment_document_count()
        assert ws.document_count == 2

    def test_increment_case_count(self) -> None:
        ws = self._make_ws()
        ws.increment_case_count()
        assert ws.case_count == 1


# ---------------------------------------------------------------------------
# SingleProcessLock
# ---------------------------------------------------------------------------

class TestSingleProcessLock:
    """Tests for SingleProcessLock."""

    def test_acquire_release(self) -> None:
        lock = SingleProcessLock()
        assert lock.acquire("ws-1")
        assert lock.is_locked("ws-1")
        lock.release("ws-1")
        assert not lock.is_locked("ws-1")

    def test_double_acquire_blocks(self) -> None:
        lock = SingleProcessLock()
        assert lock.acquire("ws-1")
        acquired = lock.acquire("ws-1", timeout=0.05)
        assert not acquired
        lock.release("ws-1")

    def test_release_without_acquire_is_safe(self) -> None:
        lock = SingleProcessLock()
        lock.release("ws-1")
        assert not lock.is_locked("ws-1")

    def test_different_workspaces_independent(self) -> None:
        lock = SingleProcessLock()
        assert lock.acquire("ws-1")
        assert lock.acquire("ws-2")
        assert lock.is_locked("ws-1")
        assert lock.is_locked("ws-2")

    def test_owner_tracking(self) -> None:
        lock = SingleProcessLock()
        assert lock.acquire("ws-1")
        owner = lock.owner("ws-1")
        assert owner is not None
        lock.release("ws-1")
        assert lock.owner("ws-1") is None

    def test_concurrent_access(self) -> None:
        lock = SingleProcessLock()
        results: list[bool] = []

        def worker() -> None:
            acquired = lock.acquire("ws-1", timeout=1.0)
            results.append(acquired)
            if acquired:
                import time
                time.sleep(0.05)
                lock.release("ws-1")

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert all(results)
        assert len(results) == 5


# ---------------------------------------------------------------------------
# Workspace events
# ---------------------------------------------------------------------------

class TestWorkspaceEvents:
    """Tests for workspace lifecycle events."""

    def test_workspace_created(self) -> None:
        e = WorkspaceCreated(aggregate_id="w1", workspace_name="Test")
        assert e.aggregate_id == "w1"
        assert e.workspace_name == "Test"
        assert e.event_id

    def test_workspace_opened(self) -> None:
        e = WorkspaceOpened(aggregate_id="w1")
        assert e.aggregate_id == "w1"

    def test_workspace_closed(self) -> None:
        e = WorkspaceClosed(aggregate_id="w1")
        assert e.aggregate_id == "w1"

    def test_workspace_archived(self) -> None:
        e = WorkspaceArchived(aggregate_id="w1")
        assert e.aggregate_id == "w1"

    def test_workspace_deleted(self) -> None:
        e = WorkspaceDeleted(aggregate_id="w1")
        assert e.aggregate_id == "w1"

    def test_workspace_validation_failed(self) -> None:
        e = WorkspaceValidationFailed(
            aggregate_id="w1",
            errors=("bad manifest",),
        )
        assert e.errors == ("bad manifest",)

    def test_workspace_migrated(self) -> None:
        e = WorkspaceMigrated(
            aggregate_id="w1",
            from_version="1.0.0",
            to_version="2.0.0",
        )
        assert e.from_version == "1.0.0"
        assert e.to_version == "2.0.0"

    def test_events_are_frozen(self) -> None:
        e = WorkspaceCreated(aggregate_id="w1")
        with pytest.raises(AttributeError):
            e.aggregate_id = "w2"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Workspace exceptions
# ---------------------------------------------------------------------------

class TestWorkspaceExceptions:
    """Tests for workspace exception hierarchy."""

    def test_base_is_lexmind_error(self) -> None:
        from lexmind.exceptions import LexMindError
        assert issubclass(WorkspaceError, LexMindError)

    def test_not_found(self) -> None:
        e = WorkspaceNotFoundError("w1")
        assert "w1" in str(e)
        assert e.workspace_id == "w1"

    def test_already_open(self) -> None:
        e = WorkspaceAlreadyOpenError("w1")
        assert "w1" in str(e)

    def test_not_open(self) -> None:
        e = WorkspaceNotOpenError("w1")
        assert "w1" in str(e)

    def test_lock_error(self) -> None:
        e = WorkspaceLockError("w1", "timeout")
        assert "timeout" in str(e)
        assert e.reason == "timeout"

    def test_lock_error_no_reason(self) -> None:
        e = WorkspaceLockError("w1")
        assert "w1" in str(e)

    def test_validation_error(self) -> None:
        e = WorkspaceValidationError("w1", details=("err1", "err2"))
        assert "err1" in str(e)
        assert e.details == ("err1", "err2")

    def test_migration_error(self) -> None:
        e = WorkspaceMigrationError("w1", "1.0", "2.0")
        assert "1.0" in str(e)
        assert "2.0" in str(e)

    def test_corrupted_error(self) -> None:
        e = WorkspaceCorruptedError("w1", "bad hash")
        assert "bad hash" in str(e)
        assert e.detail == "bad hash"

    def test_corrupted_error_no_detail(self) -> None:
        e = WorkspaceCorruptedError("w1")
        assert "w1" in str(e)


# ---------------------------------------------------------------------------
# WorkspaceManager
# ---------------------------------------------------------------------------

class TestWorkspaceManager:
    """Tests for WorkspaceManager orchestration."""

    def _make_manager(self) -> tuple[WorkspaceManager, MagicMock, MagicMock, MagicMock, MagicMock]:
        factory = MagicMock()
        loader = MagicMock()
        registry = MagicMock()
        event_bus = MagicMock()

        ws = Workspace(id="ws-001", name="Test WS")
        factory.create.return_value = ws
        loader.load.return_value = ws
        registry.get.return_value = ws
        registry.is_registered.return_value = False
        registry.list_open.return_value = [ws]

        mgr = WorkspaceManager(
            factory=factory,
            loader=loader,
            registry=registry,
            event_bus=event_bus,
        )
        return mgr, factory, loader, registry, event_bus

    def test_create_workspace(self) -> None:
        mgr, factory, _, registry, event_bus = self._make_manager()
        ws = mgr.create_workspace(name="New", owner_id="u1")
        factory.create.assert_called_once()
        registry.register.assert_called_once_with(ws)
        event_bus.publish.assert_called_once()

    def test_open_workspace(self) -> None:
        mgr, _, loader, registry, event_bus = self._make_manager()
        ws = mgr.open_workspace("ws-001")
        loader.load.assert_called_once_with("ws-001")
        registry.register.assert_called()
        assert ws.status == WorkspaceStatus.OPEN
        event_bus.publish.assert_called()

    def test_open_already_open_raises(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        registry.is_registered.return_value = True
        with pytest.raises(WorkspaceAlreadyOpenError):
            mgr.open_workspace("ws-001")

    def test_close_workspace(self) -> None:
        mgr, _, _, registry, event_bus = self._make_manager()
        ws = Workspace(id="ws-001", name="T")
        ws.open()
        ws.activate()
        registry.get.return_value = ws
        mgr.close_workspace("ws-001")
        registry.unregister.assert_called_once_with("ws-001")
        event_bus.publish.assert_called()

    def test_close_not_found_raises(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        registry.get.return_value = None
        with pytest.raises(WorkspaceNotFoundError):
            mgr.close_workspace("missing")

    def test_archive_workspace(self) -> None:
        mgr, _, _, registry, event_bus = self._make_manager()
        ws = Workspace(id="ws-001", name="T")
        ws.open()
        ws.close()
        registry.get.return_value = ws
        mgr.archive_workspace("ws-001")
        assert ws.status == WorkspaceStatus.ARCHIVED
        event_bus.publish.assert_called()

    def test_delete_workspace(self) -> None:
        mgr, _, _, registry, event_bus = self._make_manager()
        mgr.delete_workspace("ws-001")
        registry.unregister.assert_called()
        event_bus.publish.assert_called()

    def test_validate_workspace(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        ws = Workspace(id="ws-001", name="T")
        ws.manifest = WorkspaceManifest(
            workspace_id="ws-001", name="T",
        )
        registry.get.return_value = ws
        errors = mgr.validate_workspace("ws-001")
        assert errors == ()

    def test_validate_workspace_no_manifest(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        ws = Workspace(id="ws-001", name="T")
        registry.get.return_value = ws
        errors = mgr.validate_workspace("ws-001")
        assert len(errors) > 0

    def test_migrate_workspace(self) -> None:
        mgr, _, _, registry, event_bus = self._make_manager()
        ws = Workspace(id="ws-001", name="T")
        registry.get.return_value = ws
        mgr.migrate_workspace("ws-001", "2.0.0")
        assert ws.version == "2.0.0"
        event_bus.publish.assert_called()

    def test_get_workspace(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        ws = mgr.get_workspace("ws-001")
        assert ws is not None

    def test_list_open(self) -> None:
        mgr, _, _, registry, _ = self._make_manager()
        open_ws = mgr.list_open()
        assert len(open_ws) == 1

    def test_lock_acquired_on_open(self) -> None:
        factory = MagicMock()
        loader = MagicMock()
        registry = MagicMock()
        lock = MagicMock()
        lock.acquire.return_value = True

        ws = Workspace(id="ws-001", name="T")
        loader.load.return_value = ws
        registry.is_registered.return_value = False

        mgr = WorkspaceManager(
            factory=factory,
            loader=loader,
            registry=registry,
            lock=lock,
        )
        mgr.open_workspace("ws-001")
        lock.acquire.assert_called_once_with("ws-001")

    def test_lock_failure_raises(self) -> None:
        factory = MagicMock()
        loader = MagicMock()
        registry = MagicMock()
        lock = MagicMock()
        lock.acquire.return_value = False

        registry.is_registered.return_value = False

        mgr = WorkspaceManager(
            factory=factory,
            loader=loader,
            registry=registry,
            lock=lock,
        )
        with pytest.raises(WorkspaceLockError):
            mgr.open_workspace("ws-001")

    def test_no_event_bus_still_works(self) -> None:
        factory = MagicMock()
        loader = MagicMock()
        registry = MagicMock()
        ws = Workspace(id="ws-001", name="T")
        factory.create.return_value = ws
        registry.is_registered.return_value = False

        mgr = WorkspaceManager(
            factory=factory,
            loader=loader,
            registry=registry,
            event_bus=None,
        )
        result = mgr.create_workspace(name="T")
        assert result.id == "ws-001"


# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------

class TestProtocolCompliance:
    """Verify that protocols are runtime-checkable."""

    def test_workspace_lock_protocol(self) -> None:
        assert issubclass(SingleProcessLock, WorkspaceLock)

    def test_event_bus_protocol(self) -> None:
        class FakeBus:
            def publish(self, event: object) -> None:
                pass

        assert isinstance(FakeBus(), EventBus)

    def test_plugin_manager_protocol(self) -> None:
        class FakePM:
            def list_plugins(self) -> list[str]:
                return []

        assert isinstance(FakePM(), PluginManager)

    def test_logger_protocol(self) -> None:
        class FakeLog:
            def info(self, msg: str, **kwargs: object) -> None:
                pass

            def warning(self, msg: str, **kwargs: object) -> None:
                pass

            def error(self, msg: str, **kwargs: object) -> None:
                pass

        assert isinstance(FakeLog(), Logger)

    def test_storage_provider_protocol(self) -> None:
        class FakeStorage:
            def read(self, path: str) -> bytes:
                return b""

            def write(self, path: str, data: bytes) -> None:
                pass

            def exists(self, path: str) -> bool:
                return False

            def list_dir(self, path: str) -> list[str]:
                return []

        assert isinstance(FakeStorage(), StorageProvider)

    def test_configuration_protocol(self) -> None:
        class FakeConfig:
            def get(self, key: str, default: object = None) -> object:
                return default

            def set(self, key: str, value: object) -> None:
                pass

            def keys(self) -> list[str]:
                return []

        assert isinstance(FakeConfig(), Configuration)


# ---------------------------------------------------------------------------
# No infrastructure dependencies
# ---------------------------------------------------------------------------

class TestNoInfrastructureDependencies:
    """Workspace engine must not import SQL, ORM, or filesystem I/O."""

    def test_no_sql_imports(self) -> None:
        """Workspace files must not import SQL or ORM modules."""
        import inspect

        import lexmind.workspace as ws_pkg

        source = inspect.getsource(ws_pkg)
        forbidden = ["sqlite", "sqlalchemy", "psycopg", "asyncpg", "aiosqlite"]
        for mod in forbidden:
            assert mod not in source, f"Found forbidden import: {mod}"

    def test_no_fastapi_imports(self) -> None:
        """Workspace files must not import FastAPI."""
        import inspect

        import lexmind.workspace as ws_pkg

        source = inspect.getsource(ws_pkg)
        assert "fastapi" not in source

    def test_all_classes_have_docstrings(self) -> None:
        """Every public class must have a docstring."""
        import inspect

        import lexmind.workspace as ws_pkg

        public_classes = [
            obj for name, obj in inspect.getmembers(ws_pkg)
            if inspect.isclass(obj)
            and not name.startswith("_")
            and obj.__module__.startswith("lexmind.workspace")
        ]
        for cls in public_classes:
            assert cls.__doc__, f"{cls.__name__} is missing a docstring"
