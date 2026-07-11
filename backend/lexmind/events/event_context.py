"""Event context carrying traceability information."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class EventContext:
    """Optional context associated with an event."""

    correlation_id: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    workspace_id: str | None = None
    session_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    extra: dict[str, Any] = field(default_factory=dict)
