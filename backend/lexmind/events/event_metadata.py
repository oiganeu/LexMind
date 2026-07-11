"""Event metadata for diagnostics and tracing."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventMetadata:
    """Metadata describing how an event was produced and handled."""

    version: str = "1.0"
    producer: str = "unknown"
    tags: tuple[str, ...] = field(default_factory=tuple)
    retry_count: int = 0
    duration_ms: float | None = None
    experimental: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
