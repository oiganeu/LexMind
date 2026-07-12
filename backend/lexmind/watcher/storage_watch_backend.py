"""Storage-backed polling watch backend.

This backend detects changes by periodically comparing the set of
files (and their sizes) under a watched location.  All access goes
through the ``StorageManager`` abstraction, so no platform-specific
filesystem APIs are used and no path leaks outside the storage layer.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import PurePosixPath

from lexmind.storage.manager import StorageManager
from lexmind.watcher.file_event import FileEventType
from lexmind.watcher.watch_backend import BackendFileEvent
from lexmind.watcher.watch_config import WatchConfig


class StoragePollingBackend:
    """Polls a storage location and emits create/modify/delete events.

    Call :meth:`poll` to perform a comparison cycle.  A realistic
    deployment drives :meth:`poll` from a scheduler or timer; the
    backend itself remains free of any threading or OS dependencies.
    """

    def __init__(self, storage: StorageManager) -> None:
        """Initialise with a storage manager.

        Args:
            storage: The storage facade used to enumerate and stat
                     objects under each watched root.
        """
        self._storage = storage
        self._callbacks: dict[str, Callable[[BackendFileEvent], None]] = {}
        self._configs: dict[str, WatchConfig] = {}
        self._snapshots: dict[str, dict[str, int]] = {}

    def watch(
        self,
        config: WatchConfig,
        callback: Callable[[BackendFileEvent], None],
    ) -> None:
        """Begin watching *config.root_uri* from a clean snapshot."""
        self._configs[config.watch_id] = config
        self._callbacks[config.watch_id] = callback
        self._snapshots[config.watch_id] = self._snapshot(config)

    def unwatch(self, watch_id: str) -> None:
        """Stop watching *watch_id* and forget its snapshot."""
        self._configs.pop(watch_id, None)
        self._callbacks.pop(watch_id, None)
        self._snapshots.pop(watch_id, None)

    def is_watching(self, watch_id: str) -> bool:
        """Return True if *watch_id* is currently watched."""
        return watch_id in self._callbacks

    def poll(self, watch_id: str) -> None:
        """Compare the current state with the stored snapshot.

        Emits ``CREATED``, ``MODIFIED`` and ``DELETED`` events for the
        differences detected, then updates the stored snapshot.
        """
        config = self._configs.get(watch_id)
        callback = self._callbacks.get(watch_id)
        if config is None or callback is None:
            return
        previous = self._snapshots.get(watch_id, {})
        current = self._snapshot(config)
        now = time.time()
        for uri, size in current.items():
            name = PurePosixPath(uri).name
            if uri not in previous:
                callback(
                    BackendFileEvent(
                        watch_id=watch_id,
                        uri=uri,
                        name=name,
                        event_type=FileEventType.CREATED,
                        size=size,
                        timestamp=now,
                    )
                )
            elif previous[uri] != size:
                callback(
                    BackendFileEvent(
                        watch_id=watch_id,
                        uri=uri,
                        name=name,
                        event_type=FileEventType.MODIFIED,
                        size=size,
                        timestamp=now,
                    )
                )
        for uri in previous:
            if uri not in current:
                callback(
                    BackendFileEvent(
                        watch_id=watch_id,
                        uri=uri,
                        name=PurePosixPath(uri).name,
                        event_type=FileEventType.DELETED,
                        size=0,
                        timestamp=now,
                    )
                )
        self._snapshots[watch_id] = current

    def _snapshot(self, config: WatchConfig) -> dict[str, int]:
        """Return a mapping of file URI to size under *config.root_uri*.

        Directories are skipped.  When ``recursive`` is False only the
        immediate children of the root are considered.
        """
        result: dict[str, int] = {}
        stack = [config.root_uri]
        while stack:
            current = stack.pop()
            try:
                children = self._storage.list(current)
            except Exception:  # noqa: BLE001
                continue
            for name in children:
                child = f"{current.rstrip('/')}/{name}"
                stat = self._storage.stat(child)
                if stat.is_directory:
                    if config.recursive:
                        stack.append(child)
                    continue
                result[child] = stat.size
        return result
