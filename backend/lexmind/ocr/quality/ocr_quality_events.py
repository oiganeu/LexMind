"""Domain events for OCR quality assessment."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class OcrQualityStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR quality assessment begins."""

    length: int = 0
    reference_length: int = 0


@dataclass(frozen=True, slots=True)
class OcrQualityCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR quality assessment completes successfully."""

    overall_score: float = 0.0
    metric_scores: tuple[tuple[str, float], ...] = ()
    is_low_quality: bool = False


@dataclass(frozen=True, slots=True)
class OcrQualityFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR quality assessment fails."""

    error_message: str = ""
