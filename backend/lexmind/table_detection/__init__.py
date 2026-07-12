"""Table detection framework.

Detects tables and their grids on document pages through an engine-agnostic
detector contract.  The default :class:`RuleBasedTableDetector` composes with
the layout framework (it turns ``TABLE`` layout regions into
:class:`~lexmind.table_detection.table_types.TableRegion` objects), so it
works with no external dependency; model-backed detectors plug in via the
registry.  The orchestrating :class:`TableDetectionService` resolves
detectors and emits lifecycle events.
"""

from __future__ import annotations

from lexmind.table_detection.table_detection import TableDetectionService
from lexmind.table_detection.table_detection_events import (
    TableDetectionCompleted,
    TableDetectionFailed,
    TableDetectionStarted,
)
from lexmind.table_detection.table_detector import (
    DetectionTableDetector,
    RuleBasedTableDetector,
    TableDetectionEngine,
    TableDetector,
    TableDetectorNotFoundError,
    TableDetectorRegistry,
)
from lexmind.table_detection.table_plugin import TableDetectionPlugin
from lexmind.table_detection.table_types import (
    TableCell,
    TableDetectionOptions,
    TableDetectionResult,
    TableGrid,
    TableRegion,
)

__all__ = [
    "DetectionTableDetector",
    "TableCell",
    "TableDetectionCompleted",
    "TableDetectionFailed",
    "TableDetectionOptions",
    "TableDetectionPlugin",
    "TableDetectionResult",
    "TableDetectionService",
    "TableDetectionStarted",
    "TableDetector",
    "TableDetectionEngine",
    "TableDetectorNotFoundError",
    "TableDetectorRegistry",
    "TableGrid",
    "TableRegion",
    "RuleBasedTableDetector",
]
