"""Subscription records and registry."""

from dataclasses import dataclass

from lexmind.events.event_exceptions import DuplicateHandlerError
from lexmind.events.event_handler import EventHandler
from lexmind.events.event_priority import EventPriority


@dataclass
class Subscription:
    """Maps an event name to a handler."""

    event_name: str
    handler: EventHandler


class SubscriptionRegistry:
    """Tracks handlers per event name, ordered by descending priority."""

    def __init__(self) -> None:
        self._by_event: dict[str, list[EventHandler]] = {}

    def add(self, event_name: str, handler: EventHandler) -> None:
        handlers = self._by_event.setdefault(event_name, [])
        if any(h.name == handler.name for h in handlers):
            raise DuplicateHandlerError(
                f"Handler '{handler.name}' already subscribed to '{event_name}'."
            )
        handlers.append(handler)
        handlers.sort(key=lambda h: self._priority_rank(h.priority), reverse=True)

    @staticmethod
    def _priority_rank(priority: EventPriority) -> int:
        ranks = {
            EventPriority.LOW: 0,
            EventPriority.NORMAL: 1,
            EventPriority.HIGH: 2,
            EventPriority.CRITICAL: 3,
        }
        return ranks.get(priority, 1)

    def remove(self, event_name: str, handler_name: str) -> None:
        handlers = self._by_event.get(event_name, [])
        self._by_event[event_name] = [h for h in handlers if h.name != handler_name]

    def handlers_for(self, event_name: str) -> list[EventHandler]:
        return list(self._by_event.get(event_name, []))

    def clear(self) -> None:
        self._by_event.clear()

    def count(self) -> int:
        return sum(len(h) for h in self._by_event.values())
