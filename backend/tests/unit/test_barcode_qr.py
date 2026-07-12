"""Unit tests for the barcode/QR detection framework (Task 39)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.barcode_qr.barcode_qr_detection import BarcodeDetectionService
from lexmind.barcode_qr.barcode_qr_detection_events import (
    BarcodeDetectionCompleted,
    BarcodeDetectionFailed,
    BarcodeDetectionStarted,
)
from lexmind.barcode_qr.barcode_qr_detector import (
    BarcodeDetectorNotFoundError,
    BarcodeDetectorRegistry,
    DetectionBarcodeDetector,
    RuleBasedBarcodeDetector,
)
from lexmind.barcode_qr.barcode_qr_plugin import BarcodeDetectionPlugin
from lexmind.barcode_qr.barcode_qr_types import (
    BarcodeDetectionOptions,
    BarcodeDetectionResult,
    BarcodeFormat,
    BarcodeRegion,
)
from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_types import BoundingBox
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


def _region(
    code_format: BarcodeFormat = BarcodeFormat.QR,
    confidence: float = 1.0,
    payload: str = "ABC",
) -> BarcodeRegion:
    return BarcodeRegion(
        bbox=BoundingBox(0.1, 0.1, 0.3, 0.3),
        format=code_format,
        payload=payload,
        confidence=confidence,
    )


def test_barcode_region_validation() -> None:
    with pytest.raises(ValueError):
        BarcodeRegion(bbox=BoundingBox(0, 0, 1, 1), format="not-a-format")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        BarcodeRegion(bbox=BoundingBox(0, 0, 1, 1), format=BarcodeFormat.QR, confidence=2.0)
    with pytest.raises(ValueError):
        BarcodeRegion(bbox=BoundingBox(0, 0, 1, 1), format=BarcodeFormat.QR, payload=123)  # type: ignore[arg-type]
    region = BarcodeRegion(bbox=BoundingBox(0, 0, 1, 1), format=BarcodeFormat.QR)
    assert region.payload == ""
    assert region.confidence == 1.0


def test_bounding_box_validation_reused() -> None:
    with pytest.raises(ValueError):
        BarcodeRegion(bbox=BoundingBox(2, 0, 1, 1), format=BarcodeFormat.QR)


def test_result_properties() -> None:
    empty = BarcodeDetectionResult(page_number=1)
    assert empty.code_count == 0
    assert empty.is_empty
    full = BarcodeDetectionResult(
        page_number=2, regions=(_region(),), detector="rule-based"
    )
    assert full.code_count == 1
    assert not full.is_empty


def test_options_validation_and_filter() -> None:
    with pytest.raises(ValueError):
        BarcodeDetectionOptions(min_confidence=2.0)
    with pytest.raises(ValueError):
        BarcodeDetectionOptions(formats=("bad",))  # type: ignore[list-item]
    options = BarcodeDetectionOptions(min_confidence=0.5, formats=(BarcodeFormat.QR,))
    assert options.keeps(_region(BarcodeFormat.QR, 0.9))
    assert not options.keeps(_region(BarcodeFormat.QR, 0.3))
    assert not options.keeps(_region(BarcodeFormat.EAN13, 0.9))
    no_filter = BarcodeDetectionOptions()
    assert no_filter.keeps(_region(BarcodeFormat.CODE128, 0.9))


def test_rule_based_detector_returns_empty() -> None:
    detector = RuleBasedBarcodeDetector()
    assert detector.name == "rule-based"
    result = detector.detect(b"img", BarcodeDetectionOptions())
    assert isinstance(result, BarcodeDetectionResult)
    assert result.is_empty
    with pytest.raises(ValueError):
        detector.detect(b"", BarcodeDetectionOptions())


def test_registry_basics() -> None:
    registry = BarcodeDetectorRegistry()
    registry.register(RuleBasedBarcodeDetector())
    assert registry.has("rule-based")
    assert "rule-based" in registry.registered_names()
    with pytest.raises(ValueError):
        registry.register(_NamelessDetector())  # type: ignore[arg-type]
    with pytest.raises(BarcodeDetectorNotFoundError):
        registry.get("missing")


class _NamelessDetector:
    name = ""


@dataclass
class StubEngine:
    """Fake barcode detection engine."""

    regions: list

    def detect(self, image_data, options, page_number=1):
        return list(self.regions)


def test_detection_detector_filters() -> None:
    engine = StubEngine(
        regions=[
            _region(BarcodeFormat.QR, 0.9),
            _region(BarcodeFormat.EAN13, 0.2),
            _region(BarcodeFormat.CODE128, 0.9),
        ]
    )
    detector = DetectionBarcodeDetector(engine, name="stub")
    result = detector.detect(
        b"img",
        BarcodeDetectionOptions(min_confidence=0.5, formats=(BarcodeFormat.QR,)),
    )
    assert result.code_count == 1
    with pytest.raises(ValueError):
        DetectionBarcodeDetector(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        detector.detect(b"", BarcodeDetectionOptions())


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_service_emits_events() -> None:
    registry = BarcodeDetectorRegistry()
    registry.register(RuleBasedBarcodeDetector())
    bus = RecordingBus()
    service = BarcodeDetectionService(registry, event_bus=bus)
    result = service.detect(b"img", BarcodeDetectionOptions(), page_number=2)
    assert result.page_number == 2
    started = [e for e in bus.events if isinstance(e, BarcodeDetectionStarted)]
    completed = [e for e in bus.events if isinstance(e, BarcodeDetectionCompleted)]
    assert started and completed
    assert completed[0].code_count == 0


def test_service_resolves_explicit_and_default() -> None:
    registry = BarcodeDetectorRegistry()
    registry.register(RuleBasedBarcodeDetector())
    service = BarcodeDetectionService(registry, default_detector="rule-based")
    assert service.registry.registered_names() == ["rule-based"]
    assert service.detect(b"img", BarcodeDetectionOptions()).detector == "rule-based"


def test_service_missing_detector() -> None:
    bus = RecordingBus()
    service = BarcodeDetectionService(BarcodeDetectorRegistry(), event_bus=bus)
    with pytest.raises(BarcodeDetectorNotFoundError):
        service.detect(b"img", BarcodeDetectionOptions())


def test_service_failure_emits_failed() -> None:
    bus = RecordingBus()

    class BrokenDetector:
        name = "broken"

        def detect(self, image_data, options, page_number=1):
            raise RuntimeError("boom")

    registry = BarcodeDetectorRegistry()
    registry.register(BrokenDetector())  # type: ignore[arg-type]
    service = BarcodeDetectionService(registry, event_bus=bus)
    with pytest.raises(RuntimeError):
        service.detect(b"img", BarcodeDetectionOptions())
    failed = [e for e in bus.events if isinstance(e, BarcodeDetectionFailed)]
    assert failed and "boom" in failed[0].error_message


def test_plugin_wires_up() -> None:
    plugin = BarcodeDetectionPlugin()
    assert PluginCapability.BARCODE_QR_DETECTION in plugin.get_metadata().capabilities
    result = plugin.detect(b"img", BarcodeDetectionOptions())
    assert isinstance(result, BarcodeDetectionResult)
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED


def test_plugin_register_detector() -> None:
    plugin = BarcodeDetectionPlugin()
    engine = StubEngine(regions=[_region()])
    plugin.register_detector(DetectionBarcodeDetector(engine, name="custom"))
    assert plugin.registry.has("custom")
    result = plugin.detect(
        b"img", BarcodeDetectionOptions(), detector_name="custom"
    )
    assert result.code_count == 1
