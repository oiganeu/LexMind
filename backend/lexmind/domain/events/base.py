"""Base domain event."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base class for all domain events.

    Domain events are immutable records of something meaningful
    that happened in the business domain.  They are raised by
    aggregates and consumed by handlers.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: str = ""
    caused_by: str | None = None
