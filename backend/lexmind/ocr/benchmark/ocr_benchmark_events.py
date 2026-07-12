"""Domain events for OCR benchmarking."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class OcrBenchmarkStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR benchmark run begins."""

    engine_name: str = ""
    dataset_name: str = ""


@dataclass(frozen=True, slots=True)
class OcrBenchmarkCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR benchmark run completes."""

    engine_name: str = ""
    dataset_name: str = ""
    mean_accuracy: float = 0.0
    mean_latency: float = 0.0


@dataclass(frozen=True, slots=True)
class OcrBenchmarkFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when an OCR benchmark run fails."""

    engine_name: str = ""
    dataset_name: str = ""
    error_message: str = ""
