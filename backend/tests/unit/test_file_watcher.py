"""Tests for the File Watcher framework (TASK-0026).

Covers:
    - WatchConfig normalisation, validation and extension filtering
    - FileEvent / FileEventType domain types
    - InMemoryWatchBackend and StoragePollingBackend backends
    - EventBusDispatcher delivery
    - FileWatcherService: register/start/stop, create/modify/delete,
      debounce, filtering and backend independence
    - FileWatcherPlugin lifecycle
"""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from lexmind.storage.models import StorageStat
from lexmind.watcher import (
    EventBusDispatcher,
    FileEvent,
    FileEventType,
    FileWatcherPlugin,
    FileWatcherService,
    InMemoryWatchBackend,
    WatchConfig,
)
from lexmind.watcher.event_dispatcher import EventDispatcher
from lexmind.watcher.file_event import FileEvent as _FileEvent
from lexmind.watcher.storage_watch_backend import StoragePollingBackend
from lexmind.watcher.watch_backend import BackendFileEvent, WatchBackend

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeClock:
    """Controllable clock returning a configurable epoch value."""

    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeEventBus:
    """Records published events."""

    def __init__(self) -> None:
        self.published: list[object] = []

    def publish(self, event: object) -> None:
        self.published.append(event)


class FakeStorage:
    """In-memory StorageManager stand-in for the polling backend."""

    def __init__(self, root: str, files: dict[str, int]) -> None:
        self._root = root.rstrip("/")
        self._files = dict(files)
        self._dirs: set[str] = {self._root}

    @staticmethod
    def _parent(uri: str) -> str:
        base, _, _ = uri.rstrip("/").rpartition("/")
        return base

    def add_file(self, uri: str, size: int) -> None:
        self._files[uri] = size
        parent = self._parent(uri)
        while parent and parent not in self._dirs:
            self._dirs.add(parent)
            parent = self._parent(parent)

    def remove_file(self, uri: str) -> None:
        self._files.pop(uri, None)

    def list(self, uri: str = "") -> list[str]:
        target = (uri or self._root).rstrip("/")
        names: set[str] = set()
        for entry in (*self._files, *self._dirs):
            if self._parent(entry) == target:
                names.add(PurePosixPath(entry).name)
        return sorted(names)

    def stat(self, uri: str) -> StorageStat:
        if uri in self._dirs:
            return StorageStat(exists=True, is_directory=True)
        if uri in self._files:
            return StorageStat(exists=True, is_directory=False, size=self._files[uri])
        return StorageStat(exists=False)


class _CollectingDispatcher:
    """Minimal EventDispatcher that appends to a list."""

    def __init__(self, sink: list[FileEvent]) -> None:
        self._sink = sink

    def dispatch(self, event: FileEvent) -> None:
        self._sink.append(event)


# ---------------------------------------------------------------------------
# WatchConfig
# ---------------------------------------------------------------------------


class TestWatchConfig:
    def test_patterns_normalised_to_lowercase_extensions(self) -> None:
        config = WatchConfig(
            watch_id="w",
            workspace_id="ws",
            root_uri="storage://ws/inbox",
            patterns={"PDF", ".PNG", "jpg"},
        )
        assert config.patterns == {".pdf", ".png", ".jpg"}

    def test_empty_patterns_accept_everything(self) -> None:
        config = WatchConfig(
            watch_id="w", workspace_id="ws", root_uri="storage://ws/inbox"
        )
        assert config.accepts_extension("storage://ws/a.xyz")

    def test_accepts_extension_matches(self) -> None:
        config = WatchConfig(
            watch_id="w",
            workspace_id="ws",
            root_uri="storage://ws/inbox",
            patterns={".pdf"},
        )
        assert config.accepts_extension("storage://ws/doc.PDF")
        assert not config.accepts_extension("storage://ws/doc.txt")

    def test_negative_debounce_rejected(self) -> None:
        with pytest.raises(ValueError):
            WatchConfig(
                watch_id="w",
                workspace_id="ws",
                root_uri="storage://ws/inbox",
                debounce_seconds=-1.0,
            )

    def test_empty_root_rejected(self) -> None:
        with pytest.raises(ValueError):
            WatchConfig(watch_id="w", workspace_id="ws", root_uri="")

    def test_blank_pattern_is_ignored(self) -> None:
        config = WatchConfig(
            watch_id="w",
            workspace_id="ws",
            root_uri="storage://ws/in",
            patterns={"", ".pdf"},
        )
        assert config.patterns == {".pdf"}

    def test_extension_filter_property(self) -> None:
        config = WatchConfig(
            watch_id="w",
            workspace_id="ws",
            root_uri="storage://ws/in",
            patterns={".pdf"},
        )
        assert config.extension_filter == {".pdf"}


# ---------------------------------------------------------------------------
# FileEvent / FileEventType
# ---------------------------------------------------------------------------


class TestFileEvent:
    def test_event_type_values(self) -> None:
        assert FileEventType.CREATED == "created"
        assert FileEventType.MODIFIED == "modified"
        assert FileEventType.DELETED == "deleted"

    def test_file_event_is_domain_event(self) -> None:
        event = FileEvent(
            aggregate_id="ws",
            workspace_id="ws",
            watch_id="w",
            uri="storage://ws/a.pdf",
            name="a.pdf",
            event_type=FileEventType.CREATED,
            size=12,
        )
        assert event.event_id
        assert event.aggregate_id == "ws"
        assert event.event_type is FileEventType.CREATED


# ---------------------------------------------------------------------------
# InMemoryWatchBackend
# ---------------------------------------------------------------------------


class TestInMemoryWatchBackend:
    def test_watch_and_emit_delivers_to_callback(self) -> None:
        backend = InMemoryWatchBackend()
        received: list[BackendFileEvent] = []
        backend.watch(
            WatchConfig("w", "ws", "storage://ws/in"),
            received.append,
        )
        assert backend.is_watching("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a", "a", FileEventType.CREATED, 1, 0.0)
        )
        assert len(received) == 1

    def test_emit_without_callback_is_noop(self) -> None:
        backend = InMemoryWatchBackend()
        backend.emit(
            BackendFileEvent("w", "u", "a", FileEventType.CREATED, 1, 0.0)
        )

    def test_unwatch_stops_delivery(self) -> None:
        backend = InMemoryWatchBackend()
        received: list[BackendFileEvent] = []
        backend.watch(WatchConfig("w", "ws", "storage://ws/in"), received.append)
        backend.unwatch("w")
        assert not backend.is_watching("w")
        backend.emit(
            BackendFileEvent("w", "u", "a", FileEventType.CREATED, 1, 0.0)
        )
        assert received == []


# ---------------------------------------------------------------------------
# StoragePollingBackend
# ---------------------------------------------------------------------------


class TestStoragePollingBackend:
    def _backend(self, files: dict[str, int]) -> tuple[StoragePollingBackend, FakeStorage]:
        storage = FakeStorage("storage://ws/inbox", files)
        return StoragePollingBackend(storage), storage

    def test_poll_detects_created(self) -> None:
        backend, storage = self._backend({"storage://ws/inbox/a.pdf": 10})
        events: list[BackendFileEvent] = []
        backend.watch(WatchConfig("w", "ws", "storage://ws/inbox"), events.append)
        storage.add_file("storage://ws/inbox/b.pdf", 5)
        backend.poll("w")
        assert len(events) == 1
        assert events[0].event_type is FileEventType.CREATED
        assert events[0].uri.endswith("b.pdf")

    def test_poll_detects_modified(self) -> None:
        backend, storage = self._backend({"storage://ws/inbox/a.pdf": 10})
        events: list[BackendFileEvent] = []
        backend.watch(WatchConfig("w", "ws", "storage://ws/inbox"), events.append)
        storage.add_file("storage://ws/inbox/a.pdf", 99)
        backend.poll("w")
        assert len(events) == 1
        assert events[0].event_type is FileEventType.MODIFIED
        assert events[0].size == 99

    def test_poll_detects_deleted(self) -> None:
        backend, storage = self._backend({"storage://ws/inbox/a.pdf": 10})
        events: list[BackendFileEvent] = []
        backend.watch(WatchConfig("w", "ws", "storage://ws/inbox"), events.append)
        storage.remove_file("storage://ws/inbox/a.pdf")
        backend.poll("w")
        assert len(events) == 1
        assert events[0].event_type is FileEventType.DELETED

    def test_poll_is_recursive(self) -> None:
        backend, storage = self._backend({"storage://ws/inbox/a.pdf": 10})
        events: list[BackendFileEvent] = []
        backend.watch(
            WatchConfig("w", "ws", "storage://ws/inbox", recursive=True),
            events.append,
        )
        storage.add_file("storage://ws/inbox/sub/c.pdf", 3)
        backend.poll("w")
        assert any(e.uri.endswith("sub/c.pdf") for e in events)

    def test_unwatch_forgets_snapshot(self) -> None:
        backend, _ = self._backend({})
        backend.watch(WatchConfig("w", "ws", "storage://ws/inbox"), lambda e: None)
        assert backend.is_watching("w")
        backend.unwatch("w")
        assert not backend.is_watching("w")

    def test_poll_unknown_watch_is_noop(self) -> None:
        backend, _ = self._backend({})
        backend.poll("ghost")  # should not raise

    def test_snapshot_handles_list_failure(self) -> None:
        class RaisingStorage(FakeStorage):
            def list(self, uri: str = "") -> list[str]:
                raise OSError("boom")

        storage = RaisingStorage("storage://ws/inbox", {})
        backend = StoragePollingBackend(storage)
        backend.watch(WatchConfig("w", "ws", "storage://ws/inbox"), lambda e: None)
        backend.poll("w")  # snapshot empty, no events, no crash


# ---------------------------------------------------------------------------
# EventBusDispatcher
# ---------------------------------------------------------------------------


class TestEventBusDispatcher:
    def test_dispatch_publishes_to_bus(self) -> None:
        bus = FakeEventBus()
        dispatcher = EventBusDispatcher(bus)
        event = FileEvent(event_type=FileEventType.CREATED)
        dispatcher.dispatch(event)
        assert bus.published == [event]

    def test_dispatch_without_bus_is_noop(self) -> None:
        dispatcher = EventBusDispatcher(None)
        dispatcher.dispatch(FileEvent())  # should not raise


# ---------------------------------------------------------------------------
# FileWatcherService
# ---------------------------------------------------------------------------


class TestFileWatcherService:
    def test_register_then_start_watches_backend(self) -> None:
        service, backend, _ = self._service()
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        assert not service.is_watching("w")
        service.start("w")
        assert service.is_watching("w")
        assert backend.is_watching("w")

    def test_start_unknown_watch_raises(self) -> None:
        service, _, _ = self._service()
        with pytest.raises(KeyError):
            service.start("missing")

    def test_create_event_dispatched(self) -> None:
        service, backend, received = self._service()
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.CREATED, 7, 0.0)
        )
        assert len(received) == 1
        assert received[0].event_type is FileEventType.CREATED
        assert received[0].size == 7

    def test_modify_event_dispatched(self) -> None:
        service, backend, received = self._service()
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.MODIFIED, 3, 0.0)
        )
        assert received[0].event_type is FileEventType.MODIFIED

    def test_delete_event_dispatched(self) -> None:
        service, backend, received = self._service()
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.DELETED, 0, 0.0)
        )
        assert received[0].event_type is FileEventType.DELETED

    def test_extension_filter_drops_unsupported(self) -> None:
        service, backend, received = self._service()
        service.register(
            WatchConfig("w", "ws", "storage://ws/in", patterns={".pdf"})
        )
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.txt", "a.txt", FileEventType.CREATED, 1, 0.0)
        )
        assert received == []

    def test_disabled_watch_ignored(self) -> None:
        service, backend, received = self._service()
        service.register(
            WatchConfig("w", "ws", "storage://ws/in", enabled=False)
        )
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.CREATED, 1, 0.0)
        )
        assert received == []

    def test_debounce_coalesces_rapid_changes(self) -> None:
        clock = FakeClock(0.0)
        backend = InMemoryWatchBackend()
        received: list[FileEvent] = []
        service = FileWatcherService(backend, _CollectingDispatcher(received), clock=clock)
        service.register(
            WatchConfig("w", "ws", "storage://ws/in", debounce_seconds=1.0)
        )
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.MODIFIED, 1, 0.0)
        )
        clock.now = 0.5
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.MODIFIED, 2, 0.5)
        )
        # Window has not elapsed yet: nothing dispatched.
        assert received == []
        clock.now = 2.0
        service.flush()
        assert len(received) == 1
        assert received[0].size == 2  # latest snapshot wins

    def test_debounce_zero_dispatches_immediately(self) -> None:
        clock = FakeClock(0.0)
        backend = InMemoryWatchBackend()
        received: list[FileEvent] = []
        service = FileWatcherService(backend, _CollectingDispatcher(received), clock=clock)
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.CREATED, 1, 0.0)
        )
        assert len(received) == 1

    def test_stop_flushes_and_unwatches(self) -> None:
        clock = FakeClock(0.0)
        backend = InMemoryWatchBackend()
        received: list[FileEvent] = []
        service = FileWatcherService(backend, _CollectingDispatcher(received), clock=clock)
        service.register(
            WatchConfig("w", "ws", "storage://ws/in", debounce_seconds=5.0)
        )
        service.start("w")
        backend.emit(
            BackendFileEvent("w", "storage://ws/in/a.pdf", "a.pdf", FileEventType.CREATED, 1, 0.0)
        )
        assert received == []  # buffered by debounce
        service.stop("w")
        assert len(received) == 1  # flushed on stop
        assert not service.is_watching("w")

    def test_watching_ids_reported(self) -> None:
        service, _, _ = self._service()
        service.register(WatchConfig("w", "ws", "storage://ws/in"))
        service.start("w")
        assert service.watching_ids() == ["w"]

    def test_storage_backend_drives_same_service(self) -> None:
        storage = FakeStorage("storage://ws/inbox", {"storage://ws/inbox/a.pdf": 10})
        backend = StoragePollingBackend(storage)
        received: list[FileEvent] = []
        service = FileWatcherService(backend, _CollectingDispatcher(received))
        service.register(WatchConfig("w", "ws", "storage://ws/inbox"))
        service.start("w")
        storage.add_file("storage://ws/inbox/b.pdf", 4)
        backend.poll("w")
        assert any(e.uri.endswith("b.pdf") for e in received)
        assert all(isinstance(e, _FileEvent) for e in received)

    def test_debounce_seconds_unknown_uri_returns_zero(self) -> None:
        service, _, _ = self._service()
        assert service._debounce_seconds("ghost") == 0.0

    def test_dispatch_without_config_is_noop(self) -> None:
        service, _, received = self._service()
        service._dispatch(
            BackendFileEvent("ghost", "u", "a", FileEventType.CREATED, 1, 0.0)
        )
        assert received == []

    def _service(self) -> tuple[
        FileWatcherService, InMemoryWatchBackend, list[FileEvent]
    ]:
        backend = InMemoryWatchBackend()
        received: list[FileEvent] = []
        return FileWatcherService(backend, _CollectingDispatcher(received)), backend, received


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_inmemory_satisfies_watch_backend(self) -> None:
        assert isinstance(InMemoryWatchBackend(), WatchBackend)

    def test_service_satisfies_file_watcher(self) -> None:
        from lexmind.watcher.file_watcher import FileWatcher

        assert isinstance(
            FileWatcherService(InMemoryWatchBackend(), _CollectingDispatcher([])),
            FileWatcher,
        )

    def test_event_bus_dispatcher_satisfies_protocol(self) -> None:
        assert isinstance(EventBusDispatcher(None), EventDispatcher)


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------


class TestFileWatcherPlugin:
    def test_plugin_exposes_service_and_capability(self) -> None:
        from lexmind.plugins.plugin_capability import PluginCapability

        plugin = FileWatcherPlugin(InMemoryWatchBackend(), _CollectingDispatcher([]))
        assert plugin.service is not None
        assert PluginCapability.FILE_WATCH in plugin.metadata.capabilities

    def test_plugin_stop_stops_active_watches(self) -> None:
        backend = InMemoryWatchBackend()
        plugin = FileWatcherPlugin(backend, _CollectingDispatcher([]))
        plugin.service.register(WatchConfig("w", "ws", "storage://ws/in"))
        plugin.service.start("w")
        assert plugin.service.is_watching("w")
        plugin.stop()
        assert not plugin.service.is_watching("w")
