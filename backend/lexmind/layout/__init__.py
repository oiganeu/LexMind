"""Layout analysis framework.

Detects the structural regions of document pages (text, tables, figures,
headers, ...) through an engine-agnostic analyzer contract.  A pure
rule-based analyzer is provided for dependency-free use; model-backed
analyzers can be injected via the :class:`LayoutAnalyzerRegistry`.  The
orchestrating :class:`LayoutAnalysisService` resolves analyzers, optionally
merges overlapping regions and emits lifecycle events.
"""

from __future__ import annotations

from lexmind.layout.layout_analysis import LayoutAnalysisService
from lexmind.layout.layout_analyzer import (
    DetectionLayoutAnalyzer,
    LayoutAnalyzer,
    LayoutAnalyzerNotFoundError,
    LayoutAnalyzerRegistry,
    LayoutDetectionEngine,
    RuleBasedLayoutAnalyzer,
)
from lexmind.layout.layout_events import (
    LayoutAnalysisCompleted,
    LayoutAnalysisFailed,
    LayoutAnalysisStarted,
)
from lexmind.layout.layout_plugin import LayoutAnalysisPlugin
from lexmind.layout.layout_types import (
    BoundingBox,
    LayoutAnalysisOptions,
    LayoutRegion,
    LayoutResult,
    RegionType,
)

__all__ = [
    "BoundingBox",
    "DetectionLayoutAnalyzer",
    "LayoutAnalysisCompleted",
    "LayoutAnalysisFailed",
    "LayoutAnalysisPlugin",
    "LayoutAnalysisService",
    "LayoutAnalysisStarted",
    "LayoutAnalyzer",
    "LayoutAnalyzerNotFoundError",
    "LayoutAnalyzerRegistry",
    "LayoutAnalysisOptions",
    "LayoutDetectionEngine",
    "LayoutRegion",
    "LayoutResult",
    "RegionType",
    "RuleBasedLayoutAnalyzer",
]
