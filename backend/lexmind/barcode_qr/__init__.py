"""Barcode & QR detection framework.

Locates barcodes and QR codes on document pages and decodes their payloads
through an engine-agnostic detector contract.  The default
:class:`RuleBasedBarcodeDetector` is dependency-free and returns an empty
result, serving as a safe registration target; model-backed readers plug in
via :class:`DetectionBarcodeDetector` and the registry.  The orchestrating
:class:`BarcodeDetectionService` resolves detectors and emits lifecycle events.
"""

from __future__ import annotations

from lexmind.barcode_qr.barcode_qr_detection import BarcodeDetectionService
from lexmind.barcode_qr.barcode_qr_detection_events import (
    BarcodeDetectionCompleted,
    BarcodeDetectionFailed,
    BarcodeDetectionStarted,
)
from lexmind.barcode_qr.barcode_qr_detector import (
    BarcodeDetectionEngine,
    BarcodeDetector,
    BarcodeDetectorNotFoundError,
    BarcodeDetectorRegistry,
    DetectionBarcodeDetector,
    RuleBasedBarcodeDetector,
)
from lexmind.barcode_qr.barcode_qr_plugin import BarcodeDetectionPlugin
from lexmind.barcode_qr.barcode_qr_types import (
    BarcodeDetectionOptions,
    BarcodeDetectionResult,
    BarcodeFormat,
    BarcodeRegion,
)

__all__ = [
    "BarcodeDetectionCompleted",
    "BarcodeDetectionEngine",
    "BarcodeDetectionFailed",
    "BarcodeDetectionOptions",
    "BarcodeDetectionPlugin",
    "BarcodeDetectionResult",
    "BarcodeDetectionService",
    "BarcodeDetectionStarted",
    "BarcodeDetector",
    "BarcodeDetectorNotFoundError",
    "BarcodeDetectorRegistry",
    "BarcodeFormat",
    "BarcodeRegion",
    "DetectionBarcodeDetector",
    "RuleBasedBarcodeDetector",
]
