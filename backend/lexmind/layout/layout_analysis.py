"""Layout analysis service.

The :class:`LayoutAnalysisService` orchestrates layout analysis: it resolves
an analyzer from the registry, runs it, optionally merges overlapping
regions, and publishes lifecycle events.  It implements the
:class:`LayoutAnalyzer` Protocol itself, so it can be used transparently
wherever an analyzer is expected.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_analyzer import (
    LayoutAnalyzer,
    LayoutAnalyzerNotFoundError,
    LayoutAnalyzerRegistry,
)
from lexmind.layout.layout_events import (
    LayoutAnalysisCompleted,
    LayoutAnalysisFailed,
    LayoutAnalysisStarted,
)
from lexmind.layout.layout_types import (
    BoundingBox,
    LayoutAnalysisOptions,
    LayoutRegion,
    LayoutResult,
)

logger = structlog.get_logger(__name__)


class LayoutAnalysisService:
    """Default layout analysis orchestrator."""

    def __init__(
        self,
        registry: LayoutAnalyzerRegistry,
        event_bus: EventBus | None = None,
        default_analyzer: str | None = None,
    ) -> None:
        """Initialise with a registry and optional bus/default.

        Args:
            registry: Registry of available analyzers.
            event_bus: Optional bus for lifecycle events.
            default_analyzer: Name of the analyzer to use when none is
                requested.  Defaults to the first registered analyzer.
        """
        self._registry = registry
        self._event_bus = event_bus
        self._default = default_analyzer

    @property
    def registry(self) -> LayoutAnalyzerRegistry:
        """Return the analyzer registry."""
        return self._registry

    def _resolve(self, analyzer_name: str | None) -> LayoutAnalyzer:
        name = analyzer_name or self._default or self._registry.registered_names()[0]
        return self._registry.get(name)

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    @staticmethod
    def _merge_overlapping(regions: tuple[LayoutRegion, ...]) -> tuple[LayoutRegion, ...]:
        """Drop lower-confidence regions contained in higher-confidence ones."""
        ordered = sorted(regions, key=lambda r: r.confidence, reverse=True)
        kept: list[LayoutRegion] = []
        for region in ordered:
            if any(
                _contains(kept_region.bbox, region.bbox) for kept_region in kept
            ):
                continue
            kept.append(region)
        kept.sort(key=lambda r: r.order)
        return tuple(kept)

    def analyze(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions,
        page_number: int = 1,
        analyzer_name: str | None = None,
    ) -> LayoutResult:
        """Analyze *image_data* using the resolved analyzer.

        Args:
            image_data: Raw page image bytes.
            options: Analysis options (filters, merge flag).
            page_number: Page identifier for events.
            analyzer_name: Optional explicit analyzer name.

        Returns:
            A :class:`LayoutResult` with the detected (and possibly merged)
            regions.

        Raises:
            LayoutAnalyzerNotFoundError: If no analyzer can be resolved.
            ValueError: If *image_data* is empty.
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        self._emit(
            LayoutAnalysisStarted(
                aggregate_id=str(page_number),
                page_number=page_number,
            )
        )
        try:
            analyzer = self._resolve(analyzer_name)
        except IndexError as exc:
            raise LayoutAnalyzerNotFoundError(
                "No layout analyzer registered"
            ) from exc

        try:
            result = analyzer.analyze(image_data, options, page_number=page_number)
            regions = result.regions
            if options.merge_overlapping:
                regions = self._merge_overlapping(regions)
            merged = LayoutResult(
                page_number=result.page_number,
                regions=regions,
                analyzer=result.analyzer,
                image_width=result.image_width,
                image_height=result.image_height,
            )
            self._emit(
                LayoutAnalysisCompleted(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    region_count=merged.region_count,
                    analyzer=merged.analyzer,
                )
            )
            return merged
        except Exception as exc:  # noqa: BLE001 - surface as analysis failure
            self._emit(
                LayoutAnalysisFailed(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    error_message=str(exc),
                )
            )
            logger.error("layout_analysis_failed", page_number=page_number, error=str(exc))
            raise


def _contains(outer: BoundingBox, inner: BoundingBox) -> bool:
    """Return True if *outer* fully contains *inner* (normalized boxes)."""
    return (
        inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x + inner.width <= outer.x + outer.width
        and inner.y + inner.height <= outer.y + outer.height
    )
