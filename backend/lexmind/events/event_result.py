"""Result of dispatching an event to a single handler."""

from dataclasses import dataclass
from typing import Any


@dataclass
class EventResult:
    """Outcome of a handler invocation."""

    handler_name: str
    success: bool
    duration_ms: float
    error: str | None = None
    output: Any = None
