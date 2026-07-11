"""Timeline aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Timeline:
    """Timeline aggregate root.

    Manages chronological events for a case, enforcing ordering
    and preventing duplicate events.
    """

    case_id: str = ""
    _events: tuple[TimelineEvent, ...] = field(default_factory=tuple)

    @property
    def event_count(self) -> int:
        """Return the number of events."""
        return len(self._events)

    @property
    def event_ids(self) -> tuple[str, ...]:
        """Return all event IDs."""
        return tuple(e.id for e in self._events)

    def add_event(self, event: TimelineEvent) -> None:
        """Add an event to the timeline.

        Raises:
            InvariantViolationError: If the event is already on the timeline.
        """
        if any(e.id == event.id for e in self._events):
            raise InvariantViolationError(
                f"Event '{event.id}' already on timeline"
            )
        self._events = (*self._events, event)
        self._reorder()

    def remove_event(self, event_id: str) -> None:
        """Remove an event from the timeline."""
        self._events = tuple(e for e in self._events if e.id != event_id)
        self._reorder()

    def ordered_events(self) -> list[TimelineEvent]:
        """Return events in chronological order."""
        return sorted(self._events, key=lambda e: e.event_order)

    def _reorder(self) -> None:
        """Assign sequential order numbers."""
        for idx, event in enumerate(
            sorted(self._events, key=lambda e: e.date or ""), start=1
        ):
            event.event_order = idx
