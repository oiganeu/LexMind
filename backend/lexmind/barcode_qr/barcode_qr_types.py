"""Barcode and QR detection value objects.

Barcode and QR detection locates machine-readable codes on a document page and
decodes their payloads.  A :class:`BarcodeRegion` carries the code location
(a normalised :class:`~lexmind.layout.layout_types.BoundingBox`), its
:class:`BarcodeFormat`, the decoded *payload* and a *confidence* score.  All
objects are engine-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique

from lexmind.layout.layout_types import BoundingBox


@unique
class BarcodeFormat(StrEnum):
    """Supported machine-readable code formats."""

    QR = "qr"
    CODE128 = "code128"
    EAN13 = "ean13"
    CODE39 = "code39"
    DATA_MATRIX = "data_matrix"
    PDF417 = "pdf417"
    AZTEC = "aztec"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BarcodeRegion:
    """A single detected barcode/QR code on a page."""

    bbox: BoundingBox
    format: BarcodeFormat
    payload: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.format, BarcodeFormat):
            raise ValueError("format must be a BarcodeFormat")
        if not isinstance(self.payload, str):
            raise ValueError("payload must be a string")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class BarcodeDetectionResult:
    """Outcome of a barcode/QR detection run for one page."""

    page_number: int
    regions: tuple[BarcodeRegion, ...] = field(default_factory=tuple)
    detector: str = ""

    @property
    def code_count(self) -> int:
        """Return the number of detected codes."""
        return len(self.regions)

    @property
    def is_empty(self) -> bool:
        """Return True if no codes were detected."""
        return not self.regions


@dataclass(frozen=True, slots=True)
class BarcodeDetectionOptions:
    """Declarative request for barcode/QR detection.

    Attributes:
        min_confidence: Drop codes below this confidence (0-1).
        formats: Code formats to keep (empty = keep all).
    """

    min_confidence: float = 0.0
    formats: tuple[BarcodeFormat, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        for code_format in self.formats:
            if not isinstance(code_format, BarcodeFormat):
                raise ValueError("formats must contain only BarcodeFormat values")

    def keeps(self, region: BarcodeRegion) -> bool:
        """Return True if *region* passes the configured filters."""
        below_confidence = region.confidence < self.min_confidence
        wrong_format = bool(self.formats) and region.format not in self.formats
        return not (below_confidence or wrong_format)
