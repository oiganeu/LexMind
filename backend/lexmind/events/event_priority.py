"""Event priority levels."""

from enum import StrEnum


class EventPriority(StrEnum):
    """Priority used to order event dispatch."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
