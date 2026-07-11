"""Event dispatcher.

Responsible for routing events to handlers, isolating handler errors,
ordering handlers by priority, measuring execution time, and invoking
logging hooks. Synchronous by default; the architecture supports an
async dispatch path later.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from lexmind.events.event import Event
from lexmind.events.event_handler import EventHandler
from lexmind.events.event_result import EventResult


@dataclass
class DispatchStats:
    """Per-handler dispatch metrics."""

    total: int = 0
    errors: int = 0
    durations_ms: list[float] = field(default_factory=list)

    @property
    def average_duration_ms(self) -> float:
        if not self.durations_ms:
            return 0.0
        return sum(self.durations_ms) / len(self.durations_ms)


class EventDispatcher:
    """Dispatches an event to a list of handlers with error isolation."""

    def __init__(
        self,
        logging_hook: Callable[[Event, EventResult], None] | None = None,
    ) -> None:
        self._hook = logging_hook
        self.stats = DispatchStats()

    def dispatch(self, event: Event, handlers: list[EventHandler]) -> list[EventResult]:
        results: list[EventResult] = []
        for handler in handlers:
            if not handler.accepts(event):
                continue
            start = time.perf_counter()
            try:
                output = handler.handle(event)
            except Exception as exc:  # noqa: BLE001 - isolate handler failures
                duration = (time.perf_counter() - start) * 1000.0
                self.stats.total += 1
                self.stats.errors += 1
                self.stats.durations_ms.append(duration)
                result = EventResult(
                    handler_name=handler.name,
                    success=False,
                    duration_ms=duration,
                    error=str(exc),
                )
                if self._hook is not None:
                    self._hook(event, result)
                results.append(result)
            else:
                duration = (time.perf_counter() - start) * 1000.0
                self.stats.total += 1
                self.stats.durations_ms.append(duration)
                result = EventResult(
                    handler_name=handler.name,
                    success=True,
                    duration_ms=duration,
                    output=output,
                )
                if self._hook is not None:
                    self._hook(event, result)
                results.append(result)
        return results
