"""Event Bus.

Provides publish/subscribe/unsubscribe and diagnostics. Implemented
synchronously with an architecture that supports asynchronous dispatch
in the future. No external dependencies.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from lexmind.events.event import Event
from lexmind.events.event_dispatcher import EventDispatcher
from lexmind.events.event_handler import EventHandler, FunctionHandler
from lexmind.events.event_priority import EventPriority
from lexmind.events.event_registry import EventRegistry
from lexmind.events.event_result import EventResult
from lexmind.events.subscriptions import SubscriptionRegistry


@dataclass
class BusStatistics:
    """Aggregated diagnostics for the event bus."""

    published: int = 0
    dropped: int = 0
    handler_invocations: int = 0
    errors: int = 0

    @property
    def average_handler_duration_ms(self) -> float:
        return self._dispatcher_avg

    _dispatcher_avg: float = 0.0


class EventBus:
    """Central publish/subscribe coordinator."""

    def __init__(self) -> None:
        self._registry = EventRegistry()
        self._subscriptions = SubscriptionRegistry()
        self._dispatcher = EventDispatcher(logging_hook=self._on_dispatch)
        self._stats = BusStatistics()
        self._published_history: list[Event] = []

    @property
    def statistics(self) -> BusStatistics:
        self._stats._dispatcher_avg = self._dispatcher.stats.average_duration_ms
        return self._stats

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        self._registry.register(event_name)
        self._subscriptions.add(event_name, handler)

    def subscribe_fn(
        self,
        event_name: str,
        fn: Callable[[Event], Any],
        name: str | None = None,
        priority: EventPriority = EventPriority.NORMAL,
        event_filter: Callable[[Event], bool] | None = None,
    ) -> FunctionHandler:
        handler = FunctionHandler(
            name=str(name or getattr(fn, "__name__", "handler")),
            fn=fn,
            priority=priority,
            event_filter=event_filter,
        )
        self.subscribe(event_name, handler)
        return handler

    def unsubscribe(self, event_name: str, handler_name: str) -> None:
        self._subscriptions.remove(event_name, handler_name)

    def clear(self) -> None:
        self._subscriptions.clear()

    def handlers(self, event_name: str) -> list[EventHandler]:
        return self._subscriptions.handlers_for(event_name)

    def publish(self, event: Event) -> list[EventResult]:
        handlers = self._subscriptions.handlers_for(event.name)
        if not handlers:
            self._stats.dropped += 1
            return []
        self._stats.published += 1
        self._published_history.append(event)
        results = self._dispatcher.dispatch(event, handlers)
        self._stats.handler_invocations += len(results)
        self._stats.errors = self._dispatcher.stats.errors
        return results

    def history(self) -> list[Event]:
        return list(self._published_history)

    def _on_dispatch(self, event: Event, result: EventResult) -> None:
        # Reserved for logging hooks. Currently a no-op sink.
        return None
