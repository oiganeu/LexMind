"""Barcode/QR detector contract, registry and concrete detectors.

A :class:`BarcodeDetector` locates machine-readable codes on a page and decodes
their payloads.  The rule-based detector is dependency-free: it acts as a stub
that yields an empty result, serving as a safe default until a real
code-reading engine is injected.  Model-backed detection is provided by
:class:`DetectionBarcodeDetector`, which wraps an injected
:class:`BarcodeDetectionEngine`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog

from lexmind.barcode_qr.barcode_qr_types import (
    BarcodeDetectionOptions,
    BarcodeDetectionResult,
    BarcodeFormat,
    BarcodeRegion,
)

logger = structlog.get_logger(__name__)


@runtime_checkable
class BarcodeDetector(Protocol):
    """Detects barcodes and QR codes on a page."""

    @property
    def name(self) -> str:
        """Return the unique detector name."""
        ...

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions,
        page_number: int = 1,
    ) -> BarcodeDetectionResult:
        """Detect codes in *image_data* and return the result."""
        ...


@runtime_checkable
class BarcodeDetectionEngine(Protocol):
    """Low-level barcode/QR reader (typically a trained model or library)."""

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions,
        page_number: int = 1,
    ) -> list[BarcodeRegion]:
        """Return raw detected code regions for one page."""
        ...


class BarcodeDetectorNotFoundError(ValueError):
    """Raised when no detector is registered for a name."""


class RuleBasedBarcodeDetector:
    """Dependency-free stub detector.

    The rule-based path has no external dependency: without an underlying
    code-reading engine it cannot locate codes, so it always returns an empty
    result.  It exists as a safe default and as a registration target for
    real detectors through the registry.
    """

    @property
    def name(self) -> str:
        """Return the detector name."""
        return "rule-based"

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions,
        page_number: int = 1,
    ) -> BarcodeDetectionResult:
        """Return an empty result (no code-reading engine is wired in)."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        logger.info("barcode_rule_based", page_number=page_number, codes=0)
        return BarcodeDetectionResult(
            page_number=page_number,
            regions=(),
            detector=self.name,
        )


class DetectionBarcodeDetector:
    """Detector backed by an injected barcode/QR detection engine."""

    def __init__(
        self,
        engine: BarcodeDetectionEngine,
        name: str = "detection",
    ) -> None:
        """Initialise with a detection engine."""
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine
        self._name = name

    @property
    def name(self) -> str:
        """Return the detector name."""
        return self._name

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions,
        page_number: int = 1,
    ) -> BarcodeDetectionResult:
        """Run the detection engine and filter results by *options*."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        raw = self._engine.detect(image_data, options, page_number=page_number)
        regions = tuple(r for r in raw if options.keeps(r))
        logger.info("barcode_detection", detector=self._name, codes=len(regions))
        return BarcodeDetectionResult(
            page_number=page_number,
            regions=regions,
            detector=self._name,
        )


class BarcodeDetectorRegistry:
    """Registry mapping detector names to :class:`BarcodeDetector` instances."""

    def __init__(self) -> None:
        self._detectors: dict[str, BarcodeDetector] = {}

    def register(self, detector: BarcodeDetector) -> None:
        """Register a detector under its ``name``."""
        if not detector.name:
            raise ValueError("detector name must not be empty")
        self._detectors[detector.name] = detector

    def get(self, name: str) -> BarcodeDetector:
        """Return the detector registered under *name*."""
        detector = self._detectors.get(name)
        if detector is None:
            raise BarcodeDetectorNotFoundError(
                f"No barcode detector registered under '{name}'"
            )
        return detector

    def has(self, name: str) -> bool:
        """Return True if a detector is registered under *name*."""
        return name in self._detectors

    def registered_names(self) -> list[str]:
        """Return the registered detector names."""
        return sorted(self._detectors)


__all__ = [
    "BarcodeDetectionEngine",
    "BarcodeDetector",
    "BarcodeDetectorNotFoundError",
    "BarcodeDetectorRegistry",
    "BarcodeFormat",
    "DetectionBarcodeDetector",
    "RuleBasedBarcodeDetector",
]
