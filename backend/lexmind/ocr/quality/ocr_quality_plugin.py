"""OCR quality plugin.

Exposes the OCR quality framework through the plugin system.  Wraps an
:class:`~lexmind.ocr.quality.ocr_quality.OcrQualityService` backed by a
:class:`~lexmind.ocr.quality.quality_calculator.QualityCalculatorRegistry`
pre-populated with the dependency-free rule-based calculators, and declares
:class:`PluginCapability.OCR_QUALITY_METRICS`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.quality.ocr_quality import OcrQualityEngine, OcrQualityService
from lexmind.ocr.quality.quality_calculator import (
    ConfidenceMetricCalculator,
    LengthMetricCalculator,
    QualityCalculatorRegistry,
    QualityMetricCalculator,
    WhitespaceMetricCalculator,
)
from lexmind.ocr.quality.quality_types import (
    OcrQualityOptions,
    OcrQualityReport,
)
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OcrQualityPlugin(BasePlugin):
    """Plugin providing OCR quality metrics."""

    def __init__(
        self,
        registry: QualityCalculatorRegistry | None = None,
        event_bus: EventBus | None = None,
        engine: OcrQualityEngine | None = None,
        plugin_id: str = "ocr-quality",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Calculator registry.  Defaults to a registry pre-populated
                with the dependency-free rule-based calculators.
            event_bus: Optional bus for lifecycle events.
            engine: Optional aggregation hook for the overall score.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="OCR Quality",
            version="1.0.0",
            description="Computes composable quality metrics for OCR output.",
            capabilities=(PluginCapability.OCR_QUALITY_METRICS,),
        )
        if registry is None:
            registry = QualityCalculatorRegistry()
            registry.register(ConfidenceMetricCalculator())
            registry.register(LengthMetricCalculator())
            registry.register(WhitespaceMetricCalculator())
        self._service = OcrQualityService(registry, event_bus=event_bus, engine=engine)

    @property
    def service(self) -> OcrQualityService:
        """Return the underlying quality service."""
        return self._service

    @property
    def registry(self) -> QualityCalculatorRegistry:
        """Return the calculator registry."""
        return self._service.registry

    def score(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> OcrQualityReport:
        """Assess *ocr_text* and return a quality report."""
        return self._service.score(ocr_text, reference=reference, options=options)

    def register_calculator(self, calculator: QualityMetricCalculator) -> None:
        """Register an additional calculator (e.g. a model-backed one)."""
        self._service.registry.register(calculator)

    def get_calculator(self, name: str) -> QualityMetricCalculator:
        """Return a registered calculator by *name*."""
        return self._service.registry.get(name)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
