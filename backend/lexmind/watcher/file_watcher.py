"""File watcher orchestration.

``FileWatcherService`` ties a pluggable :class:`WatchBackend` to an
:class:`EventDispatcher`.  For every raw backend notification it:

    * drops changes that do not match the configured file-type filter;
    * coalesces bursts of changes to the same file into a single,
      trailing event after a configurable debounce window;
    * emits a :class:`FileEvent` through the dispatcher.

The service depends only on the ``WatchBackend`` and ``EventDispatcher``
Protocols, so it is independent of any concrete backend or message bus.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from lexmind.watcher.event_dispatcher import EventDispatcher
from lexmind.watcher.file_event import FileEvent, FileEventType
from lexmind.watcher.watch_backend import BackendFileEvent, WatchBackend
from lexmind.watcher.watch_config import WatchConfig


@dataclass
class _Pending:
    """A buffered backend event awaiting the end of its debounce window."""

    timestamp: float
    event: BackendFileEvent


@runtime_checkable
class FileWatcher(Protocol):
    """Public contract of the file watcher framework."""

    def register(self, config: WatchConfig) -> None:
        """Register a watch configuration (inactive until started)."""
        ...

    def start(self, watch_id: str) -> None:
        """Begin watching the location described by *watch_id*."""
        ...

    def stop(self, watch_id: str) -> None:
        """Stop watching *watch_id* and flush buffered events."""
        ...

    def is_watching(self, watch_id: str) -> bool:
        """Return True if *watch_id* is currently active."""
        ...

    def watching_ids(self) -> list[str]:
        """Return the identifiers of all currently active watches."""
        ...

    def flush(self) -> None:
        """Dispatch every buffered event regardless of its timer."""
        ...


class FileWatcherService:
    """Default ``FileWatcher`` implementation.

    Args:
        backend: Pluggable backend that detects raw changes.
        dispatcher: Delivers emitted ``FileEvent`` instances.
        clock: Callable returning the current epoch seconds.  Injected
               for deterministic testing; defaults to ``time.monotonic``.
    """

    def __init__(
        self,
        backend: WatchBackend,
        dispatcher: EventDispatcher,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._backend = backend
        self._dispatcher = dispatcher
        self._clock = clock
        self._configs: dict[str, WatchConfig] = {}
        self._pending: dict[str, _Pending] = {}
        self._watching: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, config: WatchConfig) -> None:
        """Register *config* for later activation via :meth:`start`."""
        self._configs[config.watch_id] = config

    def start(self, watch_id: str) -> None:
        """Begin watching the location for *watch_id*.

        Raises:
            KeyError: If no configuration was registered for *watch_id*.
        """
        config = self._require_config(watch_id)
        self._backend.watch(config, self._on_backend_event)
        self._watching.add(watch_id)

    def stop(self, watch_id: str) -> None:
        """Stop watching *watch_id* and flush any buffered events."""
        self._backend.unwatch(watch_id)
        self._watching.discard(watch_id)
        self.flush()

    def is_watching(self, watch_id: str) -> bool:
        """Return True when *watch_id* is currently active."""
        return watch_id in self._watching

    def watching_ids(self) -> list[str]:
        """Return the identifiers of all currently active watches."""
        return list(self._watching)

    def flush(self) -> None:
        """Dispatch every buffered event immediately."""
        self._drain(self._clock(), force=True)

    # ------------------------------------------------------------------
    # Backend callback
    # ------------------------------------------------------------------

    def _on_backend_event(self, raw: BackendFileEvent) -> None:
        """Buffer a raw backend event after filtering, then drain."""
        config = self._configs.get(raw.watch_id)
        if config is None or not config.enabled:
            return
        if not config.accepts_extension(raw.uri):
            return
        now = self._clock()
        self._pending[raw.uri] = _Pending(timestamp=now, event=raw)
        self._drain(now)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_config(self, watch_id: str) -> WatchConfig:
        """Return the config for *watch_id* or raise ``KeyError``."""
        config = self._configs.get(watch_id)
        if config is None:
            raise KeyError(f"Unknown watch_id: {watch_id}")
        return config

    def _drain(self, now: float, force: bool = False) -> None:
        """Dispatch buffered events whose debounce window has elapsed.

        Args:
            now: Current time used to evaluate debounce windows.
            force: When True, ignore debounce and dispatch everything
                   (used by :meth:`flush` and on shutdown).
        """
        due = [
            uri
            for uri, pending in self._pending.items()
            if force or now - pending.timestamp >= self._debounce_seconds(uri)
        ]
        for uri in due:
            pending = self._pending.pop(uri)
            self._dispatch(pending.event)

    def _debounce_seconds(self, uri: str) -> float:
        """Return the debounce window for the watch owning *uri*."""
        pending = self._pending.get(uri)
        if pending is None:
            return 0.0
        config = self._configs.get(pending.event.watch_id)
        return config.debounce_seconds if config is not None else 0.0

    def _dispatch(self, raw: BackendFileEvent) -> None:
        """Build and deliver a ``FileEvent`` from a raw notification."""
        config = self._configs.get(raw.watch_id)
        if config is None:
            return
        event = FileEvent(
            aggregate_id=config.workspace_id,
            workspace_id=config.workspace_id,
            watch_id=raw.watch_id,
            uri=raw.uri,
            name=raw.name,
            event_type=raw.event_type or FileEventType.CREATED,
            size=raw.size,
        )
        self._dispatcher.dispatch(event)
