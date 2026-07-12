"""Unit tests for the table detection framework (Task 38)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_types import (
    BoundingBox,
    LayoutRegion,
    LayoutResult,
    RegionType,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState
from lexmind.table_detection.table_detection import TableDetectionService
from lexmind.table_detection.table_detection_events import (
    TableDetectionCompleted,
    TableDetectionFailed,
    TableDetectionStarted,
)
from lexmind.table_detection.table_detector import (
    DetectionTableDetector,
    RuleBasedTableDetector,
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


def _table_region(bbox, confidence: float = 1.0) -> TableRegion:
    return TableRegion(
        bbox=bbox,
        grid=TableGrid(rows=1, columns=1),
        confidence=confidence,
    )


def _layout_region(region_type: str, bbox, confidence: float = 1.0) -> LayoutRegion:
    return LayoutRegion(
        region_type=RegionType(region_type),
        bbox=bbox,
        confidence=confidence,
    )


class FakeTableLayoutAnalyzer:
    """Layout analyzer that reports a single full-page table region."""

    name = "fake-table"

    def analyze(self, image_data, options, page_number=1):
        return LayoutResult(
            page_number=page_number,
            regions=(_layout_region("table", BoundingBox(0.1, 0.1, 0.8, 0.8)),),
            analyzer=self.name,
        )


def test_table_types_validation() -> None:
    with pytest.raises(ValueError):
        TableCell(row=-1, column=0, bbox=BoundingBox(0, 0, 1, 1))
    with pytest.raises(ValueError):
        TableRegion(bbox=BoundingBox(0, 0, 1, 1), grid=TableGrid(1, 1), confidence=2.0)
    grid = TableGrid(rows=2, columns=2, cells=(TableCell(0, 0, BoundingBox(0, 0, 0.5, 0.5)),))
    assert grid.cell_count == 1
    assert grid.cell_at(0, 0) is not None
    assert grid.cell_at(1, 1) is None


def test_options_validation_and_filter() -> None:
    with pytest.raises(ValueError):
        TableDetectionOptions(min_confidence=2.0)
    options = TableDetectionOptions(min_confidence=0.5)
    assert options.keeps(0.9)
    assert not options.keeps(0.3)


def test_rule_based_detector_finds_tables() -> None:
    detector = RuleBasedTableDetector(FakeTableLayoutAnalyzer())
    assert detector.name == "rule-based"
    result = detector.detect(b"img", TableDetectionOptions())
    assert isinstance(result, TableDetectionResult)
    assert result.table_count == 1
    assert result.tables[0].grid.cell_count == 1

    no_cells = detector.detect(b"img", TableDetectionOptions(detect_cells=False))
    assert no_cells.tables[0].grid.rows == 0


def test_rule_based_detector_filters_and_validates() -> None:
    class LowConfidenceAnalyzer:
        name = "low"

        def analyze(self, image_data, options, page_number=1):
            return LayoutResult(
                page_number=page_number,
                regions=(_layout_region("table", BoundingBox(0, 0, 1, 1), 0.2),),
                analyzer=self.name,
            )

    detector = RuleBasedTableDetector(LowConfidenceAnalyzer())
    low = detector.detect(b"img", TableDetectionOptions(min_confidence=0.9))
    assert low.is_empty

    import pytest

    with pytest.raises(ValueError):
        RuleBasedTableDetector(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        detector.detect(b"", TableDetectionOptions())


def test_registry_basics() -> None:
    registry = TableDetectorRegistry()
    registry.register(RuleBasedTableDetector(FakeTableLayoutAnalyzer()))
    assert registry.has("rule-based")
    with pytest.raises(TableDetectorNotFoundError):
        registry.get("missing")


@dataclass
class StubEngine:
    """Fake table detection engine."""

    regions: list

    def detect(self, image_data, options, page_number=1):
        return list(self.regions)


def test_detection_detector_filters() -> None:
    engine = StubEngine(
        regions=[
            _table_region(BoundingBox(0.1, 0.1, 0.5, 0.5), 0.9),
            _table_region(BoundingBox(0.2, 0.2, 0.3, 0.3), 0.2),
        ]
    )
    detector = DetectionTableDetector(engine, name="stub")
    result = detector.detect(b"img", TableDetectionOptions(min_confidence=0.5))
    assert result.table_count == 1

    import pytest

    with pytest.raises(ValueError):
        DetectionTableDetector(None)  # type: ignore[arg-type]


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_service_emits_events() -> None:
    registry = TableDetectorRegistry()
    registry.register(RuleBasedTableDetector(FakeTableLayoutAnalyzer()))
    bus = RecordingBus()
    service = TableDetectionService(registry, event_bus=bus)
    result = service.detect(b"img", TableDetectionOptions(), page_number=2)
    assert result.page_number == 2
    started = [e for e in bus.events if isinstance(e, TableDetectionStarted)]
    completed = [e for e in bus.events if isinstance(e, TableDetectionCompleted)]
    assert started and completed
    assert completed[0].table_count == 1


def test_service_missing_detector() -> None:
    bus = RecordingBus()
    service = TableDetectionService(TableDetectorRegistry(), event_bus=bus)
    with pytest.raises(TableDetectorNotFoundError):
        service.detect(b"img", TableDetectionOptions())


def test_service_failure_emits_failed() -> None:
    bus = RecordingBus()

    class BrokenDetector:
        name = "broken"

        def detect(self, image_data, options, page_number=1):
            raise RuntimeError("boom")

    registry = TableDetectorRegistry()
    registry.register(BrokenDetector())  # type: ignore[arg-type]
    service = TableDetectionService(registry, event_bus=bus)
    with pytest.raises(RuntimeError):
        service.detect(b"img", TableDetectionOptions())
    failed = [e for e in bus.events if isinstance(e, TableDetectionFailed)]
    assert failed and "boom" in failed[0].error_message


def test_plugin_wires_up() -> None:
    plugin = TableDetectionPlugin()
    assert PluginCapability.TABLE_DETECTION in plugin.get_metadata().capabilities
    result = plugin.detect(b"img", TableDetectionOptions())
    assert isinstance(result, TableDetectionResult)
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED
