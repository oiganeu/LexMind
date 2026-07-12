"""Language detection service.

The :class:`LanguageDetectionService` orchestrates language detection: it
resolves a detector from the registry, runs it and publishes lifecycle events.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.language_detection.language_detection_events import (
    LanguageDetectionCompleted,
    LanguageDetectionFailed,
    LanguageDetectionStarted,
)
from lexmind.language_detection.language_detection_types import (
    LanguageDetectionOptions,
    LanguageDetectionResult,
)
from lexmind.language_detection.language_detector import (
    LanguageDetector,
    LanguageDetectorNotFoundError,
    LanguageDetectorRegistry,
)

logger = structlog.get_logger(__name__)


class LanguageDetectionService:
    """Default language detection orchestrator."""

    def __init__(
        self,
        registry: LanguageDetectorRegistry,
        event_bus: EventBus | None = None,
        default_detector: str | None = None,
    ) -> None:
        """Initialise with a registry and optional bus/default.

        Args:
            registry: Registry of available detectors.
            event_bus: Optional bus for lifecycle events.
            default_detector: Name of the detector to use when none is
                requested.  Defaults to the first registered detector.
        """
        self._registry = registry
        self._event_bus = event_bus
        self._default = default_detector

    @property
    def registry(self) -> LanguageDetectorRegistry:
        """Return the detector registry."""
        return self._registry

    def _resolve(self, detector_name: str | None) -> LanguageDetector:
        name = detector_name or self._default or self._registry.registered_names()[0]
        return self._registry.get(name)

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions | None = None,
        detector_name: str | None = None,
    ) -> LanguageDetectionResult:
        """Detect languages in *text* using the resolved detector.

        Args:
            text: Input text to analyse.
            options: Detection options (filters).
            detector_name: Optional explicit detector name.

        Returns:
            A :class:`LanguageDetectionResult`.

        Raises:
            LanguageDetectorNotFoundError: If no detector can be resolved.
            ValueError: If *text* is empty.
        """
        if not text:
            raise ValueError("text must not be empty")

        self._emit(LanguageDetectionStarted())
        try:
            detector = self._resolve(detector_name)
        except IndexError as exc:
            raise LanguageDetectorNotFoundError(
                "No language detector registered"
            ) from exc

        try:
            result = detector.detect(text, options)
            self._emit(
                LanguageDetectionCompleted(
                    language_count=len(result.languages),
                    detector=result.detector,
                )
            )
            return result
        except Exception as exc:  # noqa: BLE001 - surface as detection failure
            self._emit(
                LanguageDetectionFailed(
                    error_message=str(exc),
                )
            )
            logger.error("language_detection_failed", error=str(exc))
            raise
