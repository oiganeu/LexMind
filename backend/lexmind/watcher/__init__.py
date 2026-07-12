"""File watcher domain types.

This subpackage defines the framework for monitoring configured
directories and emitting file events independently of any concrete
filesystem notification mechanism (inotify, fsevents, polling, ...).

The four framework components are:

    - ``FileEvent``        : the event emitted when a file changes
    - ``WatchBackend``     : pluggable backend that detects raw changes
    - ``EventDispatcher``  : delivers ``FileEvent`` instances downstream
    - ``FileWatcher``      : orchestrates backends, debouncing and filtering

All I/O is performed through injected collaborators (a ``WatchBackend``
and an ``EventDispatcher``); the domain layer therefore has no direct
dependency on the operating system or any storage provider.
"""

from __future__ import annotations

from lexmind.watcher.event_dispatcher import (
    EventBusDispatcher,
    EventDispatcher,
)
from lexmind.watcher.file_event import FileEvent, FileEventType
from lexmind.watcher.file_watcher import (
    FileWatcher,
    FileWatcherService,
)
from lexmind.watcher.plugins.file_watcher_plugin import FileWatcherPlugin
from lexmind.watcher.watch_backend import (
    BackendFileEvent,
    InMemoryWatchBackend,
    WatchBackend,
)
from lexmind.watcher.watch_config import WatchConfig

__all__ = [
    "BackendFileEvent",
    "EventBusDispatcher",
    "EventDispatcher",
    "FileEvent",
    "FileEventType",
    "FileWatcher",
    "FileWatcherPlugin",
    "FileWatcherService",
    "InMemoryWatchBackend",
    "WatchBackend",
    "WatchConfig",
]
