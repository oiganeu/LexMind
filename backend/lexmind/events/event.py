"""Event model."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from lexmind.events.event_context import EventContext
from lexmind.events.event_metadata import EventMetadata
from lexmind.events.event_priority import EventPriority
from lexmind.events.event_types import EventType


@dataclass
class Event:
    """A message published on the event bus."""

    name: str
    source_module: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    version: str = "1.0"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: EventContext = field(default_factory=EventContext)
    metadata: EventMetadata = field(default_factory=EventMetadata)

    @property
    def event_type(self) -> EventType | None:
        """Return the canonical EventType if the name matches one."""
        try:
            return EventType(self.name)
        except ValueError:
            return None

    def is_canonical(self) -> bool:
        """Return True if the event name matches a declared EventType."""
        return self.event_type is not None
