"""Event handler interface and base implementation."""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from lexmind.events.event import Event
from lexmind.events.event_priority import EventPriority


@runtime_checkable
class EventHandler(Protocol):
    """Contract for objects that handle events."""

    name: str
    enabled: bool
    priority: EventPriority

    def accepts(self, event: Event) -> bool: ...

    def handle(self, event: Event) -> Any: ...


class FunctionHandler:
    """Adapter wrapping a plain callable as an EventHandler."""

    def __init__(
        self,
        name: str,
        fn: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        enabled: bool = True,
        event_filter: Callable[[Event], bool] | None = None,
    ) -> None:
        self.name = name
        self._fn = fn
        self.priority = priority
        self.enabled = enabled
        self._filter = event_filter

    def accepts(self, event: Event) -> bool:
        """Return True if this handler should process the event."""
        return self.enabled and (self._filter is None or self._filter(event))

    def handle(self, event: Event) -> Any:
        return self._fn(event)
