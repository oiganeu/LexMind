"""OCR quality service.

The :class:`OcrQualityService` runs every enabled
:class:`~lexmind.ocr.quality.quality_calculator.QualityMetricCalculator`,
aggregates their weighted scores into an overall result and publishes
lifecycle events through an injected
:class:`~lexmind.events.event_bus.EventBus`.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.ocr.quality.ocr_quality_events import (
    OcrQualityCompleted,
    OcrQualityFailed,
    OcrQualityStarted,
)
from lexmind.ocr.quality.quality_calculator import (
    OcrQualityEngine,
    QualityCalculatorRegistry,
)
from lexmind.ocr.quality.quality_types import (
    OcrQualityOptions,
    OcrQualityReport,
    QualityMetric,
)

logger = structlog.get_logger(__name__)


class OcrQualityService:
    """Default OCR quality orchestrator."""

    def __init__(
        self,
        registry: QualityCalculatorRegistry,
        event_bus: EventBus | None = None,
        engine: OcrQualityEngine | None = None,
    ) -> None:
        """Initialise with a registry and optional bus/aggregation engine.

        Args:
            registry: Registry of available calculators.
            event_bus: Optional bus for lifecycle events.
            engine: Optional aggregation hook for the overall score.
        """
        self._registry = registry
        self._event_bus = event_bus
        self._engine = engine

    @property
    def registry(self) -> QualityCalculatorRegistry:
        """Return the calculator registry."""
        return self._registry

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _aggregate(
        self,
        metrics: list[QualityMetric],
        options: OcrQualityOptions,
    ) -> float:
        if self._engine is not None:
            return self._engine.aggregate(metrics, options)
        total_weight = sum(metric.weight for metric in metrics)
        if total_weight <= 0.0:
            return 0.0
        return sum(metric.score * metric.weight for metric in metrics) / total_weight

    def score(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> OcrQualityReport:
        """Assess *ocr_text* and return an :class:`OcrQualityReport`.

        Every enabled calculator is run; a calculator that raises is skipped
        and recorded in the report warnings so a single bad metric cannot fail
        the whole assessment.  ``OcrQualityStarted`` /
        ``OcrQualityCompleted`` are emitted on success; on any unexpected
        error ``OcrQualityFailed`` is emitted and the error is re-raised.

        Args:
            ocr_text: OCR output to assess.
            reference: Optional ground-truth text (passed to calculators).
            options: Assessment options (threshold, enabled metrics).

        Returns:
            A populated :class:`OcrQualityReport`.

        Raises:
            Exception: The original error after ``OcrQualityFailed`` is emitted.
        """
        options = options or OcrQualityOptions()
        self._emit(
            OcrQualityStarted(
                aggregate_id="ocr-quality",
                length=len(ocr_text),
                reference_length=len(reference or ""),
            )
        )
        try:
            metrics: list[QualityMetric] = []
            warnings: list[str] = []
            for name in self._registry.registered_names():
                if not options.is_enabled(name):
                    continue
                calculator = self._registry.get(name)
                try:
                    metric = calculator.calculate(
                        ocr_text, reference=reference, options=options
                    )
                except Exception as exc:  # noqa: BLE001 - isolate bad calculators
                    message = f"{name} failed: {exc}"
                    warnings.append(message)
                    logger.warning("ocr_quality_calculator_failed", calculator=name, error=str(exc))
                    continue
                metrics.append(metric)

            overall = self._aggregate(metrics, options)
            report = OcrQualityReport.build(
                metrics=tuple(metrics),
                threshold=options.threshold,
                warnings=tuple(warnings),
                overall_score=overall,
            )
            self._emit(
                OcrQualityCompleted(
                    aggregate_id="ocr-quality",
                    overall_score=report.overall_score,
                    metric_scores=tuple((m.name, m.score) for m in report.metrics),
                    is_low_quality=report.is_low_quality,
                )
            )
            return report
        except Exception as exc:  # noqa: BLE001 - surface as quality failure
            self._emit(
                OcrQualityFailed(
                    aggregate_id="ocr-quality",
                    error_message=str(exc),
                )
            )
            logger.error("ocr_quality_failed", error=str(exc))
            raise
