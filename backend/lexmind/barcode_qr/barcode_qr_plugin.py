"""Barcode/QR detection plugin.

Exposes the barcode/QR detection framework through the plugin system.  Wraps a
:class:`BarcodeDetectionService` (backed by a
:class:`~lexmind.barcode_qr.barcode_qr_detector.BarcodeDetectorRegistry`) and
declares :class:`PluginCapability.BARCODE_QR_DETECTION`.
"""

from __future__ import annotations

from lexmind.barcode_qr.barcode_qr_detection import BarcodeDetectionService
from lexmind.barcode_qr.barcode_qr_detector import (
    BarcodeDetector,
    BarcodeDetectorRegistry,
    RuleBasedBarcodeDetector,
)
from lexmind.barcode_qr.barcode_qr_types import (
    BarcodeDetectionOptions,
    BarcodeDetectionResult,
)
from lexmind.events.event_bus import EventBus
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class BarcodeDetectionPlugin(BasePlugin):
    """Plugin providing barcode/QR detection."""

    def __init__(
        self,
        registry: BarcodeDetectorRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "barcode-qr-detection",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Detector registry.  Defaults to a registry pre-populated
                with the dependency-free :class:`RuleBasedBarcodeDetector`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="Barcode/QR Detection",
            version="1.0.0",
            description="Locates and decodes barcodes and QR codes on document pages.",
            capabilities=(PluginCapability.BARCODE_QR_DETECTION,),
        )
        if registry is None:
            registry = BarcodeDetectorRegistry()
            registry.register(RuleBasedBarcodeDetector())
        self._service = BarcodeDetectionService(registry, event_bus=event_bus)

    @property
    def service(self) -> BarcodeDetectionService:
        """Return the underlying detection service."""
        return self._service

    @property
    def registry(self) -> BarcodeDetectorRegistry:
        """Return the detector registry."""
        return self._service.registry

    def detect(
        self,
        image_data: bytes,
        options: BarcodeDetectionOptions | None = None,
        page_number: int = 1,
        detector_name: str | None = None,
    ) -> BarcodeDetectionResult:
        """Detect codes in *image_data* using the service."""
        options = options or BarcodeDetectionOptions()
        return self._service.detect(
            image_data,
            options,
            page_number=page_number,
            detector_name=detector_name,
        )

    def register_detector(self, detector: BarcodeDetector) -> None:
        """Register an additional detector (e.g. a model-backed one)."""
        self._service.registry.register(detector)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
