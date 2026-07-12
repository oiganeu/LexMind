"""Domain events for table detection."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class TableDetectionStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a table detection run begins."""

    page_number: int = 1


@dataclass(frozen=True, slots=True)
class TableDetectionCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a table detection run completes."""

    page_number: int = 1
    table_count: int = 0
    detector: str = ""


@dataclass(frozen=True, slots=True)
class TableDetectionFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a table detection run fails."""

    page_number: int = 1
    error_message: str = ""
