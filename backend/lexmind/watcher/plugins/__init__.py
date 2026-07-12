"""File watcher plugin package.

Concrete backend and dispatcher implementations live here so the core
framework (``lexmind.watcher``) stays backend-independent.
"""

from __future__ import annotations

from lexmind.watcher.event_dispatcher import EventBusDispatcher
from lexmind.watcher.file_watcher import (
    FileWatcher,
    FileWatcherService,
)
from lexmind.watcher.plugins.file_watcher_plugin import FileWatcherPlugin
from lexmind.watcher.storage_watch_backend import StoragePollingBackend
from lexmind.watcher.watch_backend import InMemoryWatchBackend

__all__ = [
    "EventBusDispatcher",
    "FileWatcher",
    "FileWatcherPlugin",
    "FileWatcherService",
    "InMemoryWatchBackend",
    "StoragePollingBackend",
]
