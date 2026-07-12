"""Language detection plugin.

Exposes the language detection framework through the plugin system.  Wraps a
:class:`LanguageDetectionService` (backed by a
:class:`~lexmind.language_detection.language_detector.LanguageDetectorRegistry`)
and declares :class:`PluginCapability.LANGUAGE_DETECTION`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.language_detection.language_detection import LanguageDetectionService
from lexmind.language_detection.language_detection_types import (
    LanguageDetectionOptions,
    LanguageDetectionResult,
)
from lexmind.language_detection.language_detector import (
    LanguageDetector,
    LanguageDetectorRegistry,
    RuleBasedLanguageDetector,
)
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class LanguageDetectionPlugin(BasePlugin):
    """Plugin providing language detection."""

    def __init__(
        self,
        registry: LanguageDetectorRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "language-detection",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Detector registry.  Defaults to a registry
                pre-populated with :class:`RuleBasedLanguageDetector`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="Language Detection",
            version="1.0.0",
            description="Detects the natural language(s) of text.",
            capabilities=(PluginCapability.LANGUAGE_DETECTION,),
        )
        if registry is None:
            registry = LanguageDetectorRegistry()
            registry.register(RuleBasedLanguageDetector())
        self._service = LanguageDetectionService(registry, event_bus=event_bus)

    @property
    def service(self) -> LanguageDetectionService:
        """Return the underlying detection service."""
        return self._service

    @property
    def registry(self) -> LanguageDetectorRegistry:
        """Return the detector registry."""
        return self._service.registry

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions | None = None,
        detector_name: str | None = None,
    ) -> LanguageDetectionResult:
        """Detect languages in *text* using the service."""
        return self._service.detect(
            text,
            options=options,
            detector_name=detector_name,
        )

    def register_detector(self, detector: LanguageDetector) -> None:
        """Register an additional detector (e.g. a model-backed one)."""
        self._service.registry.register(detector)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
