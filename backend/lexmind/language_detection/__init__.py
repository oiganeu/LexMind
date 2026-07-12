"""Language detection framework.

Detects the natural language(s) present in text through an engine-agnostic
detector contract.  The default :class:`RuleBasedLanguageDetector` requires
no external dependencies.  Model-backed detectors plug in via the registry.
The orchestrating :class:`LanguageDetectionService` resolves detectors and
emits lifecycle events.
"""

from __future__ import annotations

from lexmind.language_detection.language_detection import LanguageDetectionService
from lexmind.language_detection.language_detection_events import (
    LanguageDetectionCompleted,
    LanguageDetectionFailed,
    LanguageDetectionStarted,
)
from lexmind.language_detection.language_detection_plugin import (
    LanguageDetectionPlugin,
)
from lexmind.language_detection.language_detection_types import (
    DetectedLanguage,
    LanguageDetectionOptions,
    LanguageDetectionResult,
)
from lexmind.language_detection.language_detector import (
    DetectionLanguageDetector,
    LanguageDetectionEngine,
    LanguageDetector,
    LanguageDetectorNotFoundError,
    LanguageDetectorRegistry,
    RuleBasedLanguageDetector,
)

__all__ = [
    "DetectionLanguageDetector",
    "DetectedLanguage",
    "LanguageDetectionCompleted",
    "LanguageDetectionEngine",
    "LanguageDetectionFailed",
    "LanguageDetectionOptions",
    "LanguageDetectionPlugin",
    "LanguageDetectionResult",
    "LanguageDetectionService",
    "LanguageDetectionStarted",
    "LanguageDetector",
    "LanguageDetectorNotFoundError",
    "LanguageDetectorRegistry",
    "RuleBasedLanguageDetector",
]
