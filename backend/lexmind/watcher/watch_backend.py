"""Pluggable watch backends.

A ``WatchBackend`` detects raw filesystem changes for a configured
location and reports them through a callback.  Concrete backends may
use OS notification APIs, polling, or any other mechanism; the rest of
the framework only depends on the ``WatchBackend`` Protocol, which
keeps the watcher independent of any platform-specific implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from lexmind.watcher.file_event import FileEventType
from lexmind.watcher.watch_config import WatchConfig


@dataclass(frozen=True, slots=True)
class BackendFileEvent:
    """Raw change notification produced by a ``WatchBackend``.

    Attributes:
        watch_id: Identifier of the watch that produced the event.
        uri: Storage URI of the affected file.
        name: Base name of the affected file.
        event_type: Kind of change detected.
        size: Current size of the file in bytes.
        timestamp: Epoch seconds at which the change was observed.
    """

    watch_id: str
    uri: str
    name: str
    event_type: FileEventType
    size: int
    timestamp: float


@runtime_checkable
class WatchBackend(Protocol):
    """Contract implemented by every file-watching backend."""

    def watch(
        self,
        config: WatchConfig,
        callback: Callable[[BackendFileEvent], None],
    ) -> None:
        """Begin watching *config.root_uri*.

        Args:
            config: The watch configuration.
            callback: Invoked for every raw change detected.
        """
        ...

    def unwatch(self, watch_id: str) -> None:
        """Stop watching the location identified by *watch_id*."""
        ...

    def is_watching(self, watch_id: str) -> bool:
        """Return True if *watch_id* is currently being watched."""
        ...


class InMemoryWatchBackend:
    """Backend whose events are injected manually.

    Useful as a test double and as a simple programmatic source of
    synthetic events.  Call :meth:`emit` to simulate a change.
    """

    def __init__(self) -> None:
        self._callbacks: dict[str, Callable[[BackendFileEvent], None]] = {}
        self._watching: set[str] = set()

    def watch(
        self,
        config: WatchConfig,
        callback: Callable[[BackendFileEvent], None],
    ) -> None:
        """Register *callback* for *config.watch_id*."""
        self._callbacks[config.watch_id] = callback
        self._watching.add(config.watch_id)

    def unwatch(self, watch_id: str) -> None:
        """Remove the watch identified by *watch_id*."""
        self._callbacks.pop(watch_id, None)
        self._watching.discard(watch_id)

    def is_watching(self, watch_id: str) -> bool:
        """Return True if *watch_id* is registered."""
        return watch_id in self._watching

    def emit(self, event: BackendFileEvent) -> None:
        """Deliver *event* to the registered callback, if any."""
        callback = self._callbacks.get(event.watch_id)
        if callback is not None:
            callback(event)
