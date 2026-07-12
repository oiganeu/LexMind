"""Domain events for barcode/QR detection."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class BarcodeDetectionStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a barcode/QR detection run begins."""

    page_number: int = 1


@dataclass(frozen=True, slots=True)
class BarcodeDetectionCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a barcode/QR detection run completes."""

    page_number: int = 1
    code_count: int = 0
    detector: str = ""


@dataclass(frozen=True, slots=True)
class BarcodeDetectionFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a barcode/QR detection run fails."""

    page_number: int = 1
    error_message: str = ""
