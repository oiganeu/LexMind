"""Domain events for layout analysis."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class LayoutAnalysisStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a layout analysis run begins."""

    page_number: int = 1


@dataclass(frozen=True, slots=True)
class LayoutAnalysisCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a layout analysis run completes."""

    page_number: int = 1
    region_count: int = 0
    analyzer: str = ""


@dataclass(frozen=True, slots=True)
class LayoutAnalysisFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a layout analysis run fails."""

    page_number: int = 1
    error_message: str = ""
