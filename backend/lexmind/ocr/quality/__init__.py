"""OCR quality metrics framework.

Scores OCR output via composable metric calculators.  Each calculator
produces a single :class:`QualityMetric`; the
:class:`OcrQualityService` aggregates them into an
:class:`OcrQualityReport` and emits lifecycle events.
"""

from __future__ import annotations

from lexmind.ocr.quality.ocr_quality import OcrQualityService
from lexmind.ocr.quality.ocr_quality_events import (
    OcrQualityCompleted,
    OcrQualityFailed,
    OcrQualityStarted,
)
from lexmind.ocr.quality.ocr_quality_plugin import OcrQualityPlugin
from lexmind.ocr.quality.quality_calculator import (
    ConfidenceMetricCalculator,
    LengthMetricCalculator,
    QualityCalculatorNotFoundError,
    QualityCalculatorRegistry,
    QualityMetricCalculator,
    WhitespaceMetricCalculator,
)
from lexmind.ocr.quality.quality_types import (
    OcrQualityOptions,
    OcrQualityReport,
    QualityMetric,
)

__all__ = [
    "ConfidenceMetricCalculator",
    "LengthMetricCalculator",
    "OcrQualityCompleted",
    "OcrQualityFailed",
    "OcrQualityOptions",
    "OcrQualityPlugin",
    "OcrQualityReport",
    "OcrQualityService",
    "OcrQualityStarted",
    "QualityCalculatorNotFoundError",
    "QualityCalculatorRegistry",
    "QualityMetric",
    "QualityMetricCalculator",
    "WhitespaceMetricCalculator",
]
