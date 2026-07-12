"""Table detector contract, registry and concrete detectors.

A :class:`TableDetector` locates tables on a page and builds their grids.
The rule-based detector composes with the layout framework: it asks an
injected :class:`~lexmind.layout.layout_analyzer.LayoutAnalyzer` for
``TABLE`` regions and turns each into a :class:`TableRegion`.  Model-backed
detection is provided by :class:`DetectionTableDetector`, which wraps an
injected :class:`TableDetectionEngine`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog

from lexmind.layout.layout_analyzer import LayoutAnalyzer
from lexmind.layout.layout_types import LayoutAnalysisOptions, RegionType
from lexmind.table_detection.table_types import (
    TableCell,
    TableDetectionOptions,
    TableDetectionResult,
    TableGrid,
    TableRegion,
)

logger = structlog.get_logger(__name__)


@runtime_checkable
class TableDetector(Protocol):
    """Detects tables and their grids on a page."""

    @property
    def name(self) -> str:
        """Return the unique detector name."""
        ...

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions,
        page_number: int = 1,
    ) -> TableDetectionResult:
        """Detect tables in *image_data* and return the result."""
        ...


@runtime_checkable
class TableDetectionEngine(Protocol):
    """Low-level table detector (typically a trained model)."""

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions,
        page_number: int = 1,
    ) -> list[TableRegion]:
        """Return raw detected table regions for one page."""
        ...


class TableDetectorNotFoundError(Exception):
    """Raised when no detector is registered for a name."""


class RuleBasedTableDetector:
    """Dependency-free detector that builds on layout analysis.

    It uses an injected layout analyzer to find ``TABLE`` regions and emits a
    :class:`TableRegion` per match.  Without a cell-level model the grid is a
    single cell spanning the whole table; when ``detect_cells`` is disabled
    only the table bounding box is produced.
    """

    def __init__(self, layout_analyzer: LayoutAnalyzer) -> None:
        """Initialise with a layout analyzer."""
        if layout_analyzer is None:
            raise ValueError("layout_analyzer must not be None")
        self._analyzer = layout_analyzer

    @property
    def name(self) -> str:
        """Return the detector name."""
        return "rule-based"

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions,
        page_number: int = 1,
    ) -> TableDetectionResult:
        """Find TABLE regions via layout analysis and build table regions."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        layout = self._analyzer.analyze(
            image_data,
            LayoutAnalysisOptions(region_types=(RegionType.TABLE,)),
            page_number=page_number,
        )
        tables: list[TableRegion] = []
        for region in layout.regions:
            if not options.keeps(region.confidence):
                continue
            grid = (
                TableGrid(
                    rows=1,
                    columns=1,
                    cells=(TableCell(row=0, column=0, bbox=region.bbox),),
                )
                if options.detect_cells
                else TableGrid(rows=0, columns=0)
            )
            tables.append(
                TableRegion(
                    bbox=region.bbox,
                    grid=grid,
                    confidence=region.confidence,
                    page_number=page_number,
                )
            )
        logger.info("table_rule_based", page_number=page_number, tables=len(tables))
        return TableDetectionResult(
            page_number=page_number,
            tables=tuple(tables),
            detector=self.name,
        )


class DetectionTableDetector:
    """Detector backed by an injected table detection engine."""

    def __init__(
        self,
        engine: TableDetectionEngine,
        name: str = "detection",
    ) -> None:
        """Initialise with a detection engine."""
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine
        self._name = name

    @property
    def name(self) -> str:
        """Return the detector name."""
        return self._name

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions,
        page_number: int = 1,
    ) -> TableDetectionResult:
        """Run the detection engine and filter results by *options*."""
        if not image_data:
            raise ValueError("image_data must not be empty")
        raw = self._engine.detect(image_data, options, page_number=page_number)
        tables = tuple(t for t in raw if options.keeps(t.confidence))
        logger.info("table_detection", detector=self._name, tables=len(tables))
        return TableDetectionResult(
            page_number=page_number,
            tables=tables,
            detector=self._name,
        )


class TableDetectorRegistry:
    """Registry mapping detector names to :class:`TableDetector` instances."""

    def __init__(self) -> None:
        self._detectors: dict[str, TableDetector] = {}

    def register(self, detector: TableDetector) -> None:
        """Register a detector under its ``name``."""
        if not detector.name:
            raise ValueError("detector name must not be empty")
        self._detectors[detector.name] = detector

    def get(self, name: str) -> TableDetector:
        """Return the detector registered under *name*."""
        detector = self._detectors.get(name)
        if detector is None:
            raise TableDetectorNotFoundError(
                f"No table detector registered under '{name}'"
            )
        return detector

    def has(self, name: str) -> bool:
        """Return True if a detector is registered under *name*."""
        return name in self._detectors

    def registered_names(self) -> list[str]:
        """Return the registered detector names."""
        return sorted(self._detectors)
