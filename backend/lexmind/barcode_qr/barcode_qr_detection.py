"""Barcode/QR detection service.

The :class:`BarcodeDetectionService` orchestrates barcode/QR detection: it
resolves a detector from the registry, runs it and publishes lifecycle events.
It implements the :class:`BarcodeDetector` Protocol itself so it can be used
transparently wherever a detector is expected.
"""

from __future__ import annotations

import structlog

from lexmind.barcode_qr.barcode_qr_detection_events import (
    BarcodeDetectionCompleted,
    BarcodeDetectionFailed,
    BarcodeDetectionStarted,
)
from lexmind.barcode_qr.barcode_qr_detector import (
    BarcodeDetector,
    BarcodeDetectorNotFoundError,
    BarcodeDetectorRegistry,
)
from lexmind.barcode_qr.barcode_qr_types import (
    BarcodeDetectionOptions,
    BarcodeDetectionResult,
)
from lexmind.events.event_bus import EventBus

logger = structlog.get_logger(__name__)


class BarcodeDetectionService:
    """Default barcode/QR detection orchestrator."""

    def __init__(
        self,
        registry: BarcodeDetectorRegistry,
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
    def registry(self) -> BarcodeDetectorRegistry:
        """Return the detector registry."""
        return self._registry

    def _resolve(self, detector_name: str | None) -> BarcodeDetector:
        name = detector_name or self._default or self._registry.registered_names()[0]
        return self._registry.get(name)

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions,
        page_number: int = 1,
        detector_name: str | None = None,
    ) -> BarcodeDetectionResult:
        """Detect codes in *image_data* using the resolved detector.

        Args:
            image_data: Raw page image bytes.
            options: Detection options (filters).
            page_number: Page identifier for events.
            detector_name: Optional explicit detector name.

        Returns:
            A :class:`BarcodeDetectionResult`.

        Raises:
            BarcodeDetectorNotFoundError: If no detector can be resolved.
            ValueError: If *image_data* is empty.
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        self._emit(
            BarcodeDetectionStarted(
                aggregate_id=str(page_number),
                page_number=page_number,
            )
        )
        try:
            detector = self._resolve(detector_name)
        except IndexError as exc:
            raise BarcodeDetectorNotFoundError(
                "No barcode detector registered"
            ) from exc

        try:
            result = detector.detect(image_data, options, page_number=page_number)
            self._emit(
                BarcodeDetectionCompleted(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    code_count=result.code_count,
                    detector=result.detector,
                )
            )
            return result
        except Exception as exc:  # noqa: BLE001 - surface as detection failure
            self._emit(
                BarcodeDetectionFailed(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    error_message=str(exc),
                )
            )
            logger.error("barcode_detection_failed", page_number=page_number, error=str(exc))
            raise
