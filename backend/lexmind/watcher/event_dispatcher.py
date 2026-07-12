"""Event dispatcher abstraction.

The ``FileWatcher`` never talks to the EventBus directly; instead it
delegates delivery to an ``EventDispatcher``.  This keeps the watcher
decoupled from the concrete messaging infrastructure and makes it easy
to substitute a different sink (log, queue, test spy) without touching
the watcher logic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lexmind.watcher.file_event import FileEvent


@runtime_checkable
class EventDispatcher(Protocol):
    """Contract for delivering ``FileEvent`` instances downstream."""

    def dispatch(self, event: FileEvent) -> None:
        """Deliver *event* to the downstream consumer(s)."""
        ...


class EventBusDispatcher:
    """Dispatcher that publishes events through the EventBus."""

    def __init__(self, event_bus: object | None) -> None:
        """Initialise with an EventBus-like collaborator.

        Args:
            event_bus: Object exposing a ``publish(event)`` method.
                       May be ``None`` to silently drop events.
        """
        self._event_bus = event_bus

    def dispatch(self, event: FileEvent) -> None:
        """Publish *event* on the configured EventBus, if present."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[attr-defined]
