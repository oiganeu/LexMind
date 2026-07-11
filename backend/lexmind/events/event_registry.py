"""Registry of known event types.

Allows validating event names against declared canonical types and
registering additional custom event types at runtime.
"""

from lexmind.events.event_exceptions import UnknownEventError
from lexmind.events.event_types import EventType


class EventRegistry:
    """Tracks valid event names."""

    def __init__(self) -> None:
        self._known: set[str] = {e.value for e in EventType}

    def register(self, event_name: str) -> None:
        self._known.add(event_name)

    def is_registered(self, event_name: str) -> bool:
        return event_name in self._known

    def validate(self, event_name: str) -> None:
        if event_name not in self._known:
            raise UnknownEventError(f"Unknown event type: '{event_name}'")

    def known_events(self) -> list[str]:
        return sorted(self._known)
