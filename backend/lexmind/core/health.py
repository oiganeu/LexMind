"""Health model for LexMind modules."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class HealthStatus(StrEnum):
    """Standard health states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class Health:
    """Health report for a module or the kernel."""

    module: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """Return True if the status is healthy."""
        return self.status == HealthStatus.HEALTHY
