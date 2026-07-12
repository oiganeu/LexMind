"""Table detection service.

The :class:`TableDetectionService` orchestrates table detection: it resolves
a detector from the registry, runs it and publishes lifecycle events.  It
implements the :class:`TableDetector` Protocol itself so it can be used
transparently wherever a detector is expected.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.table_detection.table_detection_events import (
    TableDetectionCompleted,
    TableDetectionFailed,
    TableDetectionStarted,
)
from lexmind.table_detection.table_detector import (
    TableDetector,
    TableDetectorNotFoundError,
    TableDetectorRegistry,
)
from lexmind.table_detection.table_types import (
    TableDetectionOptions,
    TableDetectionResult,
)

logger = structlog.get_logger(__name__)


class TableDetectionService:
    """Default table detection orchestrator."""

    def __init__(
        self,
        registry: TableDetectorRegistry,
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
    def registry(self) -> TableDetectorRegistry:
        """Return the detector registry."""
        return self._registry

    def _resolve(self, detector_name: str | None) -> TableDetector:
        name = detector_name or self._default or self._registry.registered_names()[0]
        return self._registry.get(name)

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions,
        page_number: int = 1,
        detector_name: str | None = None,
    ) -> TableDetectionResult:
        """Detect tables in *image_data* using the resolved detector.

        Args:
            image_data: Raw page image bytes.
            options: Detection options (filters).
            page_number: Page identifier for events.
            detector_name: Optional explicit detector name.

        Returns:
            A :class:`TableDetectionResult`.

        Raises:
            TableDetectorNotFoundError: If no detector can be resolved.
            ValueError: If *image_data* is empty.
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        self._emit(
            TableDetectionStarted(
                aggregate_id=str(page_number),
                page_number=page_number,
            )
        )
        try:
            detector = self._resolve(detector_name)
        except IndexError as exc:
            raise TableDetectorNotFoundError(
                "No table detector registered"
            ) from exc

        try:
            result = detector.detect(image_data, options, page_number=page_number)
            self._emit(
                TableDetectionCompleted(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    table_count=result.table_count,
                    detector=result.detector,
                )
            )
            return result
        except Exception as exc:  # noqa: BLE001 - surface as detection failure
            self._emit(
                TableDetectionFailed(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    error_message=str(exc),
                )
            )
            logger.error("table_detection_failed", page_number=page_number, error=str(exc))
            raise
