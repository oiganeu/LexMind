"""Domain events for the OCR pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class OcrPipelineStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR pipeline run begins."""

    page_number: int = 1
    step_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OcrPipelineStepCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted after each OCR pipeline step completes successfully."""

    page_number: int = 1
    step_name: str = ""
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class OcrPipelineCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR pipeline run finishes successfully."""

    page_number: int = 1
    step_count: int = 0
    final_text: str = ""
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class OcrPipelineFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR pipeline run fails on a step."""

    page_number: int = 1
    step_name: str = ""
    error_message: str = ""
