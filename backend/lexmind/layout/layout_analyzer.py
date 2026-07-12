"""Layout analyzer contract, registry and concrete analyzers.

A :class:`LayoutAnalyzer` detects the structural regions of a document page.
The contract is engine-agnostic: concrete analyzers either use a pure
rule-based strategy (no dependencies, fully testable) or wrap an injected
:class:`LayoutDetectionEngine` (e.g. a deep-learning layout model loaded
lazily).  The :class:`LayoutAnalyzerRegistry` resolves analyzers by name.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog

from lexmind.layout.layout_types import LayoutAnalysisOptions, LayoutRegion, LayoutResult

logger = structlog.get_logger(__name__)


@runtime_checkable
class LayoutAnalyzer(Protocol):
    """Detects layout regions of a page."""

    @property
    def name(self) -> str:
        """Return the unique analyzer name."""
        ...

    def analyze(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions,
        page_number: int = 1,
    ) -> LayoutResult:
        """Analyze *image_data* and return detected regions."""
        ...


@runtime_checkable
class LayoutDetectionEngine(Protocol):
    """Low-level region detector (typically a trained model)."""

    def detect(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions,
        page_number: int = 1,
    ) -> list[LayoutRegion]:
        """Return raw detected regions for one page."""
        ...


class LayoutAnalyzerNotFoundError(Exception):
    """Raised when no analyzer is registered for a name."""


class RuleBasedLayoutAnalyzer:
    """Dependency-free analyzer that treats the whole page as text.

    This is a safe default and a building block: with no model available it
    assumes a single full-page text block.  It still honours the configured
    region-type and confidence filters, so it composes with the service.
    """

    def __init__(self, region_type: str = "text") -> None:
        """Initialise with the region type to emit."""
        if not region_type:
            raise ValueError("region_type must not be empty")
        self._region_type = region_type

    @property
    def name(self) -> str:
        """Return the analyzer name."""
        return "rule-based"

    def analyze(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions,
        page_number: int = 1,
    ) -> LayoutResult:
        """Return a single full-page region filtered by *options*."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        from lexmind.layout.layout_types import BoundingBox, RegionType

        region = LayoutRegion(
            region_type=RegionType(self._region_type),
            bbox=BoundingBox(x=0.0, y=0.0, width=1.0, height=1.0),
            confidence=1.0,
            page_number=page_number,
            order=0,
        )
        regions = tuple(r for r in (region,) if options.keeps(r))
        logger.info("layout_rule_based", page_number=page_number, kept=len(regions))
        return LayoutResult(
            page_number=page_number,
            regions=regions,
            analyzer=self.name,
        )


class DetectionLayoutAnalyzer:
    """Analyzer backed by an injected detection engine (e.g. a model)."""

    def __init__(
        self,
        engine: LayoutDetectionEngine,
        name: str = "detection",
    ) -> None:
        """Initialise with a detection engine."""
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine
        self._name = name

    @property
    def name(self) -> str:
        """Return the analyzer name."""
        return self._name

    def analyze(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions,
        page_number: int = 1,
    ) -> LayoutResult:
        """Run the detection engine and filter regions by *options*."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        raw = self._engine.detect(image_data, options, page_number=page_number)
        regions = tuple(r for r in raw if options.keeps(r))
        logger.info("layout_detection", analyzer=self._name, kept=len(regions))
        return LayoutResult(
            page_number=page_number,
            regions=regions,
            analyzer=self._name,
        )


class LayoutAnalyzerRegistry:
    """Registry mapping analyzer names to :class:`LayoutAnalyzer` instances."""

    def __init__(self) -> None:
        self._analyzers: dict[str, LayoutAnalyzer] = {}

    def register(self, analyzer: LayoutAnalyzer) -> None:
        """Register an analyzer under its ``name``."""
        if not analyzer.name:
            raise ValueError("analyzer name must not be empty")
        self._analyzers[analyzer.name] = analyzer

    def get(self, name: str) -> LayoutAnalyzer:
        """Return the analyzer registered under *name*."""
        analyzer = self._analyzers.get(name)
        if analyzer is None:
            raise LayoutAnalyzerNotFoundError(
                f"No layout analyzer registered under '{name}'"
            )
        return analyzer

    def has(self, name: str) -> bool:
        """Return True if an analyzer is registered under *name*."""
        return name in self._analyzers

    def registered_names(self) -> list[str]:
        """Return the registered analyzer names."""
        return sorted(self._analyzers)
