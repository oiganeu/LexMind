"""Tests for the OCR artifact integration framework (TASK-0045).

Covers:
    - OcrArtifact validation
    - OcrArtifactQuery.matches
    - OcrArtifactOptions.overwrite
    - InMemoryArtifactRepository: save/get/find/delete/list_all + duplicate handling
    - ArtifactRepositoryRegistry: register/get/has/missing raises
    - OcrArtifactIntegrationService: stored/deleted/failed events, duplicate raises
    - OcrArtifactIntegrationPlugin: capability, store/get/find/delete/list_all,
      register_repository, start/stop
"""

from __future__ import annotations

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.artifacts.artifact_repository import (
    ArtifactRepositoryNotFoundError,
    ArtifactRepositoryRegistry,
    DuplicateArtifactError,
    InMemoryArtifactRepository,
)
from lexmind.ocr.artifacts.artifact_types import (
    OcrArtifact,
    OcrArtifactOptions,
    OcrArtifactQuery,
)
from lexmind.ocr.artifacts.ocr_artifact_events import (
    OcrArtifactDeleted,
    OcrArtifactFailed,
    OcrArtifactStored,
)
from lexmind.ocr.artifacts.ocr_artifact_integration import (
    OcrArtifactIntegrationService,
)
from lexmind.ocr.artifacts.ocr_artifact_plugin import OcrArtifactIntegrationPlugin
from lexmind.plugins.plugin_capability import PluginCapability

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_artifact(
    artifact_id: str = "art-1",
    document_id: str = "doc-1",
    page_number: int = 1,
    text: str = "hello",
) -> OcrArtifact:
    return OcrArtifact(
        artifact_id=artifact_id,
        document_id=document_id,
        page_number=page_number,
        image_ref=None,
        text=text,
        regions=["r1"],
        tables=["t1"],
        created_at=0.0,
    )


# ---------------------------------------------------------------------------
# OcrArtifact
# ---------------------------------------------------------------------------


class TestOcrArtifact:
    def test_valid_construction(self) -> None:
        a = _make_artifact()
        assert a.artifact_id == "art-1"
        assert a.document_id == "doc-1"
        assert a.page_number == 1
        assert a.text == "hello"
        assert a.regions == ["r1"]
        assert a.tables == ["t1"]

    def test_empty_artifact_id_raises(self) -> None:
        with pytest.raises(ValueError, match="artifact_id must not be empty"):
            _make_artifact(artifact_id="")

    def test_empty_document_id_raises(self) -> None:
        with pytest.raises(ValueError, match="document_id must not be empty"):
            _make_artifact(document_id="")

    def test_page_number_below_one_raises(self) -> None:
        with pytest.raises(ValueError, match="page_number must be >= 1"):
            _make_artifact(page_number=0)

    def test_optional_fields_default(self) -> None:
        a = OcrArtifact(
            artifact_id="x",
            document_id="d",
            page_number=1,
            image_ref=None,
            text="",
        )
        assert a.regions == []
        assert a.tables == []
        assert a.created_at > 0

    def test_image_ref_optional(self) -> None:
        a = _make_artifact()
        assert a.image_ref is None

    def test_image_ref_set(self) -> None:
        a = _make_artifact()
        updated = OcrArtifact(
            artifact_id=a.artifact_id,
            document_id=a.document_id,
            page_number=a.page_number,
            image_ref="img://page1",
            text=a.text,
            regions=a.regions,
            tables=a.tables,
            created_at=a.created_at,
        )
        assert updated.image_ref == "img://page1"


# ---------------------------------------------------------------------------
# OcrArtifactQuery
# ---------------------------------------------------------------------------


class TestOcrArtifactQuery:
    def test_matches_same_document(self) -> None:
        q = OcrArtifactQuery(document_id="doc-1")
        assert q.matches(_make_artifact(document_id="doc-1"))

    def test_matches_different_document(self) -> None:
        q = OcrArtifactQuery(document_id="doc-2")
        assert not q.matches(_make_artifact(document_id="doc-1"))

    def test_matches_page_number(self) -> None:
        q = OcrArtifactQuery(document_id="doc-1", page_number=1)
        assert q.matches(_make_artifact(page_number=1))
        assert not q.matches(_make_artifact(page_number=2))

    def test_matches_no_page_filter(self) -> None:
        q = OcrArtifactQuery(document_id="doc-1")
        assert q.matches(_make_artifact(page_number=5))


# ---------------------------------------------------------------------------
# OcrArtifactOptions
# ---------------------------------------------------------------------------


class TestOcrArtifactOptions:
    def test_default_no_overwrite(self) -> None:
        opts = OcrArtifactOptions()
        assert not opts.allows_overwrite()

    def test_overwrite_true(self) -> None:
        opts = OcrArtifactOptions(overwrite=True)
        assert opts.allows_overwrite()


# ---------------------------------------------------------------------------
# InMemoryArtifactRepository
# ---------------------------------------------------------------------------


class TestInMemoryArtifactRepository:
    def test_save_and_get(self) -> None:
        repo = InMemoryArtifactRepository()
        a = _make_artifact()
        repo.save(a, overwrite=False)
        assert repo.get("art-1") is a

    def test_get_missing_returns_none(self) -> None:
        repo = InMemoryArtifactRepository()
        assert repo.get("nonexistent") is None

    def test_duplicate_raises_when_no_overwrite(self) -> None:
        repo = InMemoryArtifactRepository()
        a = _make_artifact()
        repo.save(a, overwrite=False)
        with pytest.raises(DuplicateArtifactError):
            repo.save(a, overwrite=False)

    def test_overwrite_succeeds(self) -> None:
        repo = InMemoryArtifactRepository()
        a1 = _make_artifact(text="first")
        repo.save(a1, overwrite=False)
        a2 = _make_artifact(text="second")
        repo.save(a2, overwrite=True)
        assert repo.get("art-1").text == "second"

    def test_find_matches(self) -> None:
        repo = InMemoryArtifactRepository()
        repo.save(_make_artifact(artifact_id="a1", page_number=1), overwrite=False)
        repo.save(_make_artifact(artifact_id="a2", page_number=2), overwrite=False)
        query = OcrArtifactQuery(document_id="doc-1", page_number=1)
        results = repo.find(query)
        assert len(results) == 1
        assert results[0].artifact_id == "a1"

    def test_find_no_matches(self) -> None:
        repo = InMemoryArtifactRepository()
        repo.save(_make_artifact(), overwrite=False)
        query = OcrArtifactQuery(document_id="other")
        assert repo.find(query) == []

    def test_delete_existing(self) -> None:
        repo = InMemoryArtifactRepository()
        repo.save(_make_artifact(), overwrite=False)
        assert repo.delete("art-1") is True
        assert repo.get("art-1") is None

    def test_delete_missing(self) -> None:
        repo = InMemoryArtifactRepository()
        assert repo.delete("nonexistent") is False

    def test_list_all(self) -> None:
        repo = InMemoryArtifactRepository()
        repo.save(_make_artifact(artifact_id="a1"), overwrite=False)
        repo.save(_make_artifact(artifact_id="a2"), overwrite=False)
        all_artifacts = repo.list_all()
        assert len(all_artifacts) == 2

    def test_list_all_empty(self) -> None:
        repo = InMemoryArtifactRepository()
        assert repo.list_all() == []


# ---------------------------------------------------------------------------
# ArtifactRepositoryRegistry
# ---------------------------------------------------------------------------


class TestArtifactRepositoryRegistry:
    def test_register_and_get(self) -> None:
        reg = ArtifactRepositoryRegistry()
        repo = InMemoryArtifactRepository()
        reg.register("default", repo)
        assert reg.get("default") is repo

    def test_has(self) -> None:
        reg = ArtifactRepositoryRegistry()
        assert not reg.has("default")
        reg.register("default", InMemoryArtifactRepository())
        assert reg.has("default")

    def test_registered_names(self) -> None:
        reg = ArtifactRepositoryRegistry()
        reg.register("b", InMemoryArtifactRepository())
        reg.register("a", InMemoryArtifactRepository())
        assert reg.registered_names() == ["a", "b"]

    def test_empty_name_raises(self) -> None:
        reg = ArtifactRepositoryRegistry()
        with pytest.raises(ValueError, match="repository name must not be empty"):
            reg.register("", InMemoryArtifactRepository())

    def test_missing_raises(self) -> None:
        reg = ArtifactRepositoryRegistry()
        with pytest.raises(ArtifactRepositoryNotFoundError):
            reg.get("nonexistent")


# ---------------------------------------------------------------------------
# OcrArtifactIntegrationService
# ---------------------------------------------------------------------------


class TestOcrArtifactIntegrationService:
    def test_store_emits_stored_event(self) -> None:
        bus = EventBus()
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo, event_bus=bus)
        stored_events: list[OcrArtifactStored] = []

        def _capture(event: object) -> None:
            if isinstance(event, OcrArtifactStored):
                stored_events.append(event)

        bus.subscribe_fn("ocr_artifact_stored", _capture)
        svc.store(_make_artifact())
        assert len(stored_events) == 1
        assert stored_events[0].artifact_id == "art-1"

    def test_store_duplicate_raises_and_emits_failed(self) -> None:
        bus = EventBus()
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo, event_bus=bus)
        failed_events: list[OcrArtifactFailed] = []

        def _capture(event: object) -> None:
            if isinstance(event, OcrArtifactFailed):
                failed_events.append(event)

        bus.subscribe_fn("ocr_artifact_failed", _capture)
        svc.store(_make_artifact())
        with pytest.raises(DuplicateArtifactError):
            svc.store(_make_artifact())
        assert len(failed_events) == 1
        assert failed_events[0].artifact_id == "art-1"

    def test_store_with_overwrite_succeeds(self) -> None:
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo)
        svc.store(_make_artifact(text="first"))
        svc.store(_make_artifact(text="second"), options=OcrArtifactOptions(overwrite=True))
        assert svc.get("art-1").text == "second"

    def test_delete_emits_deleted_event(self) -> None:
        bus = EventBus()
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo, event_bus=bus)
        deleted_events: list[OcrArtifactDeleted] = []

        def _capture(event: object) -> None:
            if isinstance(event, OcrArtifactDeleted):
                deleted_events.append(event)

        bus.subscribe_fn("ocr_artifact_deleted", _capture)
        svc.store(_make_artifact())
        result = svc.delete("art-1")
        assert result is True
        assert len(deleted_events) == 1

    def test_delete_missing_no_event(self) -> None:
        bus = EventBus()
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo, event_bus=bus)
        published = bus.statistics.published
        result = svc.delete("nonexistent")
        assert result is False
        assert bus.statistics.published == published

    def test_get_delegates(self) -> None:
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo)
        svc.store(_make_artifact())
        assert svc.get("art-1").artifact_id == "art-1"

    def test_find_delegates(self) -> None:
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo)
        svc.store(_make_artifact(artifact_id="a1", page_number=1))
        svc.store(_make_artifact(artifact_id="a2", page_number=2))
        results = svc.find(OcrArtifactQuery(document_id="doc-1", page_number=1))
        assert len(results) == 1

    def test_list_all_delegates(self) -> None:
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo)
        svc.store(_make_artifact(artifact_id="a1"))
        svc.store(_make_artifact(artifact_id="a2"))
        assert len(svc.list_all()) == 2

    def test_none_repository_raises(self) -> None:
        with pytest.raises(ValueError, match="repository must not be None"):
            OcrArtifactIntegrationService(None)  # type: ignore[arg-type]

    def test_no_event_bus_still_works(self) -> None:
        repo = InMemoryArtifactRepository()
        svc = OcrArtifactIntegrationService(repo, event_bus=None)
        svc.store(_make_artifact())
        assert svc.get("art-1") is not None


# ---------------------------------------------------------------------------
# OcrArtifactIntegrationPlugin
# ---------------------------------------------------------------------------


class TestOcrArtifactIntegrationPlugin:
    def test_capability(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        assert PluginCapability.OCR_ARTIFACT_INTEGRATION in plugin.capabilities

    def test_store_and_get(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        plugin.store(_make_artifact())
        assert plugin.get("art-1").artifact_id == "art-1"

    def test_find(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        plugin.store(_make_artifact(artifact_id="a1", page_number=1))
        plugin.store(_make_artifact(artifact_id="a2", page_number=2))
        results = plugin.find(OcrArtifactQuery(document_id="doc-1", page_number=1))
        assert len(results) == 1

    def test_delete(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        plugin.store(_make_artifact())
        assert plugin.delete("art-1") is True
        assert plugin.get("art-1") is None

    def test_list_all(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        plugin.store(_make_artifact(artifact_id="a1"))
        plugin.store(_make_artifact(artifact_id="a2"))
        assert len(plugin.list_all()) == 2

    def test_register_repository(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        repo = InMemoryArtifactRepository()
        plugin.register_repository("alt", repo)
        assert plugin.registry.has("alt")
        assert plugin.registry.get("alt") is repo

    def test_start_stop(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        plugin.start()
        from lexmind.plugins.plugin_state import PluginState
        assert plugin.state is PluginState.STARTED
        plugin.stop()
        assert plugin.state is PluginState.STOPPED

    def test_service_property(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        assert isinstance(plugin.service, OcrArtifactIntegrationService)

    def test_artifact_repository_property(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        assert isinstance(plugin.artifact_repository, InMemoryArtifactRepository)

    def test_registry_property(self) -> None:
        plugin = OcrArtifactIntegrationPlugin()
        assert isinstance(plugin.registry, ArtifactRepositoryRegistry)
