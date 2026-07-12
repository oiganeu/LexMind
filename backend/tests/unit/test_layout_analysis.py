"""Unit tests for the layout analysis framework (Task 37)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_analysis import LayoutAnalysisService
from lexmind.layout.layout_analyzer import (
    DetectionLayoutAnalyzer,
    LayoutAnalyzerNotFoundError,
    LayoutAnalyzerRegistry,
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
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


def _region(region_type: str, bbox, confidence: float = 1.0) -> LayoutRegion:
    return LayoutRegion(
        region_type=RegionType(region_type),
        bbox=bbox,
        confidence=confidence,
    )


def test_region_type_values() -> None:
    assert RegionType.TABLE == "table"
    assert RegionType.TEXT == "text"


def test_bounding_box_validation() -> None:
    with pytest.raises(ValueError):
        BoundingBox(x=-0.1, y=0.0, width=1.0, height=1.0)
    with pytest.raises(ValueError):
        BoundingBox(x=0.0, y=0.0, width=1.1, height=1.0)
    assert BoundingBox(0.0, 0.0, 1.0, 1.0).width == 1.0


def test_options_filtering() -> None:
    options = LayoutAnalysisOptions(
        region_types=(RegionType.TABLE,), min_confidence=0.5
    )
    assert options.keeps(_region("table", BoundingBox(0, 0, 1, 1), 0.9))
    assert not options.keeps(_region("table", BoundingBox(0, 0, 1, 1), 0.3))
    assert not options.keeps(_region("text", BoundingBox(0, 0, 1, 1), 0.9))


def test_options_validation() -> None:
    with pytest.raises(ValueError):
        LayoutAnalysisOptions(min_confidence=2.0)


def test_rule_based_analyzer() -> None:
    analyzer = RuleBasedLayoutAnalyzer()
    assert analyzer.name == "rule-based"
    result = analyzer.analyze(b"img", LayoutAnalysisOptions())
    assert isinstance(result, LayoutResult)
    assert result.region_count == 1
    assert result.regions[0].region_type is RegionType.TEXT

    filtered = analyzer.analyze(
        b"img",
        LayoutAnalysisOptions(region_types=(RegionType.TABLE,)),
    )
    assert filtered.is_empty


def test_rule_based_rejects_empty() -> None:
    with pytest.raises(ValueError):
        RuleBasedLayoutAnalyzer().analyze(b"", LayoutAnalysisOptions())


def test_registry_basics() -> None:
    registry = LayoutAnalyzerRegistry()
    registry.register(RuleBasedLayoutAnalyzer())
    assert registry.has("rule-based")
    assert registry.get("rule-based").name == "rule-based"
    assert "rule-based" in registry.registered_names()
    with pytest.raises(LayoutAnalyzerNotFoundError):
        registry.get("missing")


@dataclass
class StubEngine:
    """Fake detection engine returning fixed regions."""

    regions: list

    def detect(self, image_data, options, page_number=1):
        return list(self.regions)


def test_detection_analyzer_filters() -> None:
    engine = StubEngine(
        regions=[
            _region("table", BoundingBox(0.1, 0.1, 0.5, 0.5), 0.9),
            _region("text", BoundingBox(0.2, 0.2, 0.3, 0.3), 0.2),
        ]
    )
    analyzer = DetectionLayoutAnalyzer(engine, name="stub")
    result = analyzer.analyze(
        b"img", LayoutAnalysisOptions(min_confidence=0.5)
    )
    assert result.region_count == 1
    assert result.regions[0].region_type is RegionType.TABLE


def test_detection_analyzer_rejects_bad_args() -> None:
    import pytest

    with pytest.raises(ValueError):
        DetectionLayoutAnalyzer(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        DetectionLayoutAnalyzer(StubEngine([])).analyze(b"", LayoutAnalysisOptions())


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_service_resolves_and_emits() -> None:
    registry = LayoutAnalyzerRegistry()
    registry.register(RuleBasedLayoutAnalyzer())
    bus = RecordingBus()
    service = LayoutAnalysisService(registry, event_bus=bus)
    result = service.analyze(b"img", LayoutAnalysisOptions(), page_number=3)
    assert result.page_number == 3
    started = [e for e in bus.events if isinstance(e, LayoutAnalysisStarted)]
    completed = [e for e in bus.events if isinstance(e, LayoutAnalysisCompleted)]
    assert started and completed
    assert completed[0].page_number == 3


def test_service_merge_overlapping() -> None:
    registry = LayoutAnalyzerRegistry()
    engine = StubEngine(
        regions=[
            _region("text", BoundingBox(0.0, 0.0, 1.0, 1.0), 0.9),
            _region("text", BoundingBox(0.2, 0.2, 0.3, 0.3), 0.5),
        ]
    )
    registry.register(DetectionLayoutAnalyzer(engine, name="stub"))
    service = LayoutAnalysisService(registry, default_analyzer="stub")

    kept = service.analyze(b"img", LayoutAnalysisOptions())
    assert kept.region_count == 2

    merged = service.analyze(b"img", LayoutAnalysisOptions(merge_overlapping=True))
    assert merged.region_count == 1


def test_service_missing_analyzer() -> None:
    bus = RecordingBus()
    service = LayoutAnalysisService(LayoutAnalyzerRegistry(), event_bus=bus)
    with pytest.raises(LayoutAnalyzerNotFoundError):
        service.analyze(b"img", LayoutAnalysisOptions())


def test_service_failure_emits_failed() -> None:
    bus = RecordingBus()

    class BrokenAnalyzer:
        name = "broken"

        def analyze(self, image_data, options, page_number=1):
            raise RuntimeError("boom")

    registry = LayoutAnalyzerRegistry()
    registry.register(BrokenAnalyzer())  # type: ignore[arg-type]
    service = LayoutAnalysisService(registry, event_bus=bus)
    with pytest.raises(RuntimeError):
        service.analyze(b"img", LayoutAnalysisOptions())
    failed = [e for e in bus.events if isinstance(e, LayoutAnalysisFailed)]
    assert failed and "boom" in failed[0].error_message


def test_plugin_wires_up() -> None:
    plugin = LayoutAnalysisPlugin()
    assert PluginCapability.LAYOUT_ANALYSIS in plugin.get_metadata().capabilities
    assert plugin.registry.has("rule-based")
    result = plugin.analyze(b"img", LayoutAnalysisOptions())
    assert result.region_count == 1
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED
