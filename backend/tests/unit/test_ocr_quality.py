"""Unit tests for the OCR quality metrics framework (Task 41)."""

from __future__ import annotations

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.quality.ocr_quality import OcrQualityService
from lexmind.ocr.quality.ocr_quality_events import (
    OcrQualityCompleted,
    OcrQualityFailed,
    OcrQualityStarted,
)
from lexmind.ocr.quality.ocr_quality_plugin import OcrQualityPlugin
from lexmind.ocr.quality.quality_calculator import (
    ConfidenceMetricCalculator,
    LengthMetricCalculator,
    QualityCalculatorNotFoundError,
    QualityCalculatorRegistry,
    WhitespaceMetricCalculator,
)
from lexmind.ocr.quality.quality_types import (
    OcrQualityOptions,
    OcrQualityReport,
    QualityMetric,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState

# ---------------------------------------------------------------------------
# quality_types
# ---------------------------------------------------------------------------

class TestQualityMetricValidation:
    """QualityMetric must reject out-of-range scores and negative weights."""

    def test_valid_metric(self) -> None:
        m = QualityMetric(name="x", score=0.5, weight=1.0, details={"a": 1})
        assert m.name == "x"
        assert m.score == 0.5

    def test_score_below_zero(self) -> None:
        with pytest.raises(ValueError, match="score"):
            QualityMetric(name="x", score=-0.1)

    def test_score_above_one(self) -> None:
        with pytest.raises(ValueError, match="score"):
            QualityMetric(name="x", score=1.5)

    def test_negative_weight(self) -> None:
        with pytest.raises(ValueError, match="weight"):
            QualityMetric(name="x", score=0.5, weight=-1.0)

    def test_zero_weight_allowed(self) -> None:
        m = QualityMetric(name="x", score=0.5, weight=0.0)
        assert m.weight == 0.0

    def test_boundary_scores(self) -> None:
        low = QualityMetric(name="a", score=0.0)
        high = QualityMetric(name="b", score=1.0)
        assert low.score == 0.0
        assert high.score == 1.0


class TestOcrQualityReport:
    """OcrQualityReport aggregation and is_low_quality."""

    def test_build_weighted(self) -> None:
        m1 = QualityMetric(name="a", score=0.8, weight=2.0)
        m2 = QualityMetric(name="b", score=0.4, weight=1.0)
        report = OcrQualityReport.build(metrics=(m1, m2), threshold=0.5)
        assert abs(report.overall_score - (0.8 * 2 + 0.4 * 1) / 3) < 1e-9
        assert not report.is_low_quality

    def test_build_zero_weight(self) -> None:
        m = QualityMetric(name="a", score=0.5, weight=0.0)
        report = OcrQualityReport.build(metrics=(m,), threshold=0.5)
        assert report.overall_score == 0.0
        assert report.is_low_quality

    def test_build_empty_metrics(self) -> None:
        report = OcrQualityReport.build(metrics=(), threshold=0.5)
        assert report.overall_score == 0.0
        assert report.is_low_quality

    def test_is_low_quality_below_threshold(self) -> None:
        report = OcrQualityReport(overall_score=0.3, threshold=0.5)
        assert report.is_low_quality

    def test_is_not_low_quality_at_threshold(self) -> None:
        report = OcrQualityReport(overall_score=0.5, threshold=0.5)
        assert not report.is_low_quality

    def test_build_explicit_overall_score(self) -> None:
        m = QualityMetric(name="a", score=0.8, weight=1.0)
        report = OcrQualityReport.build(
            metrics=(m,), threshold=0.5, overall_score=0.99
        )
        assert report.overall_score == 0.99


class TestOcrQualityOptions:
    """OcrQualityOptions filtering and validation."""

    def test_threshold_validation(self) -> None:
        with pytest.raises(ValueError, match="threshold"):
            OcrQualityOptions(threshold=2.0)

    def test_is_enabled_all(self) -> None:
        opts = OcrQualityOptions()
        assert opts.is_enabled("any")
        assert opts.is_enabled("other")

    def test_is_enabled_whitelist(self) -> None:
        opts = OcrQualityOptions(enabled_metrics=("a", "b"))
        assert opts.is_enabled("a")
        assert opts.is_enabled("b")
        assert not opts.is_enabled("c")

    def test_keeps(self) -> None:
        opts = OcrQualityOptions(threshold=0.6)
        assert opts.keeps(0.7)
        assert not opts.keeps(0.4)
        assert opts.keeps(0.6)


# ---------------------------------------------------------------------------
# quality_calculator
# ---------------------------------------------------------------------------

class TestConfidenceMetricCalculator:
    """ConfidenceMetricCalculator text composition heuristic."""

    def test_empty_text(self) -> None:
        calc = ConfidenceMetricCalculator()
        m = calc.calculate("")
        assert m.score == 0.0
        assert m.name == "confidence"
        assert m.details["reason"] == "empty"

    def test_whitespace_only(self) -> None:
        calc = ConfidenceMetricCalculator()
        m = calc.calculate("   \n\t  ")
        assert m.score == 0.0
        assert m.details["reason"] == "whitespace_only"

    def test_all_alnum(self) -> None:
        calc = ConfidenceMetricCalculator()
        m = calc.calculate("abc123")
        assert m.score == 1.0

    def test_mixed_content(self) -> None:
        calc = ConfidenceMetricCalculator()
        m = calc.calculate("abc!@#")
        assert 0.0 < m.score < 1.0
        assert m.details["alnum"] == 3
        assert m.details["non_whitespace"] == 6

    def test_custom_name(self) -> None:
        calc = ConfidenceMetricCalculator(name="my_conf")
        assert calc.name == "my_conf"
        m = calc.calculate("test")
        assert m.name == "my_conf"


class TestLengthMetricCalculator:
    """LengthMetricCalculator scales linearly with expected_length."""

    def test_empty(self) -> None:
        calc = LengthMetricCalculator()
        m = calc.calculate("")
        assert m.score == 0.0
        assert m.name == "length"

    def test_short_text(self) -> None:
        calc = LengthMetricCalculator(expected_length=100)
        m = calc.calculate("a" * 50)
        assert m.score == 0.5

    def test_long_text(self) -> None:
        calc = LengthMetricCalculator(expected_length=100)
        m = calc.calculate("a" * 200)
        assert m.score == 1.0

    def test_exact_length(self) -> None:
        calc = LengthMetricCalculator(expected_length=50)
        m = calc.calculate("a" * 50)
        assert m.score == 1.0

    def test_zero_expected_length(self) -> None:
        with pytest.raises(ValueError, match="expected_length"):
            LengthMetricCalculator(expected_length=0)

    def test_custom_name(self) -> None:
        calc = LengthMetricCalculator(name="len", expected_length=10)
        assert calc.name == "len"


class TestWhitespaceMetricCalculator:
    """WhitespaceMetricCalculator decays when whitespace is excessive."""

    def test_empty(self) -> None:
        calc = WhitespaceMetricCalculator()
        m = calc.calculate("")
        assert m.score == 0.0
        assert m.name == "whitespace"

    def test_balanced(self) -> None:
        calc = WhitespaceMetricCalculator(max_whitespace_ratio=0.6)
        m = calc.calculate("hello world")
        assert m.score == 1.0

    def test_excessive_whitespace(self) -> None:
        calc = WhitespaceMetricCalculator(max_whitespace_ratio=0.3)
        m = calc.calculate("a                b")
        assert m.score < 1.0
        assert m.score >= 0.0

    def test_all_whitespace(self) -> None:
        calc = WhitespaceMetricCalculator(max_whitespace_ratio=0.5)
        m = calc.calculate("     ")
        assert m.score == 0.0

    def test_invalid_ratio(self) -> None:
        with pytest.raises(ValueError, match="max_whitespace_ratio"):
            WhitespaceMetricCalculator(max_whitespace_ratio=1.5)

    def test_custom_name(self) -> None:
        calc = WhitespaceMetricCalculator(name="ws")
        assert calc.name == "ws"


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

class TestQualityCalculatorRegistry:
    """Registry register / get / has / missing."""

    def test_register_and_get(self) -> None:
        reg = QualityCalculatorRegistry()
        calc = ConfidenceMetricCalculator()
        reg.register(calc)
        assert reg.get("confidence") is calc

    def test_register_empty_name(self) -> None:
        reg = QualityCalculatorRegistry()

        class NoName:
            name = ""
            def calculate(self, ocr_text, reference=None, options=None):
                return QualityMetric(name="", score=0.0)

        with pytest.raises(ValueError, match="empty"):
            reg.register(NoName())  # type: ignore[arg-type]

    def test_get_missing(self) -> None:
        reg = QualityCalculatorRegistry()
        with pytest.raises(QualityCalculatorNotFoundError):
            reg.get("nonexistent")

    def test_has(self) -> None:
        reg = QualityCalculatorRegistry()
        assert not reg.has("confidence")
        reg.register(ConfidenceMetricCalculator())
        assert reg.has("confidence")

    def test_registered_names(self) -> None:
        reg = QualityCalculatorRegistry()
        reg.register(WhitespaceMetricCalculator())
        reg.register(ConfidenceMetricCalculator())
        assert reg.registered_names() == ["confidence", "whitespace"]


# ---------------------------------------------------------------------------
# service
# ---------------------------------------------------------------------------

class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


class BrokenCalculator:
    """Calculator that raises on calculate."""

    name = "broken"

    def calculate(self, ocr_text, reference=None, options=None):
        raise RuntimeError("boom")


def _default_registry() -> QualityCalculatorRegistry:
    reg = QualityCalculatorRegistry()
    reg.register(ConfidenceMetricCalculator())
    reg.register(LengthMetricCalculator())
    reg.register(WhitespaceMetricCalculator())
    return reg


class TestOcrQualityService:
    """Service emits events, aggregates, and handles failures."""

    def test_score_emits_started_and_completed(self) -> None:
        bus = RecordingBus()
        service = OcrQualityService(_default_registry(), event_bus=bus)
        report = service.score("Hello world test text")
        assert isinstance(report, OcrQualityReport)
        started = [e for e in bus.events if isinstance(e, OcrQualityStarted)]
        completed = [e for e in bus.events if isinstance(e, OcrQualityCompleted)]
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0].overall_score == report.overall_score

    def test_score_completed_has_is_low_quality(self) -> None:
        bus = RecordingBus()
        service = OcrQualityService(_default_registry(), event_bus=bus)
        report = service.score("")
        completed = [e for e in bus.events if isinstance(e, OcrQualityCompleted)]
        assert completed[0].is_low_quality is True
        assert report.is_low_quality

    def test_score_respects_options(self) -> None:
        service = OcrQualityService(_default_registry())
        opts = OcrQualityOptions(enabled_metrics=("confidence",))
        report = service.score("abc123", options=opts)
        assert len(report.metrics) == 1
        assert report.metrics[0].name == "confidence"

    def test_score_calculator_failure_emits_warning(self) -> None:
        bus = RecordingBus()
        reg = QualityCalculatorRegistry()
        reg.register(BrokenCalculator())
        reg.register(ConfidenceMetricCalculator())
        service = OcrQualityService(reg, event_bus=bus)
        report = service.score("text")
        assert any("broken" in w for w in report.warnings)
        completed = [e for e in bus.events if isinstance(e, OcrQualityCompleted)]
        assert len(completed) == 1

    def test_score_all_broken_emits_zero(self) -> None:
        reg = QualityCalculatorRegistry()
        reg.register(BrokenCalculator())
        service = OcrQualityService(reg)
        report = service.score("text")
        assert report.overall_score == 0.0

    def test_score_failure_emits_failed_and_raises(self) -> None:
        bus = RecordingBus()

        class BlowUpRegistry(QualityCalculatorRegistry):
            def registered_names(self):
                raise RuntimeError("registry broken")

        service = OcrQualityService(BlowUpRegistry(), event_bus=bus)
        with pytest.raises(RuntimeError, match="registry broken"):
            service.score("text")
        failed = [e for e in bus.events if isinstance(e, OcrQualityFailed)]
        assert len(failed) == 1

    def test_score_no_bus(self) -> None:
        service = OcrQualityService(_default_registry(), event_bus=None)
        report = service.score("test text here")
        assert isinstance(report, OcrQualityReport)

    def test_score_with_reference(self) -> None:
        service = OcrQualityService(_default_registry())
        report = service.score("ocr text", reference="ref text")
        assert isinstance(report, OcrQualityReport)

    def test_registry_property(self) -> None:
        reg = _default_registry()
        service = OcrQualityService(reg)
        assert service.registry is reg

    def test_score_with_custom_engine(self) -> None:
        class FixedEngine:
            def aggregate(self, metrics, options):
                return 0.42

        service = OcrQualityService(_default_registry(), engine=FixedEngine())
        report = service.score("text")
        assert report.overall_score == 0.42


# ---------------------------------------------------------------------------
# plugin
# ---------------------------------------------------------------------------

class TestOcrQualityPlugin:
    """Plugin wires up capability, score and register_calculator."""

    def test_capability(self) -> None:
        plugin = OcrQualityPlugin()
        assert PluginCapability.OCR_QUALITY_METRICS in plugin.get_metadata().capabilities

    def test_score_returns_report(self) -> None:
        plugin = OcrQualityPlugin()
        report = plugin.score("some ocr text for testing")
        assert isinstance(report, OcrQualityReport)
        assert len(report.metrics) == 3

    def test_register_calculator(self) -> None:
        plugin = OcrQualityPlugin()
        plugin.register_calculator(BrokenCalculator())
        assert plugin.registry.has("broken")

    def test_get_calculator(self) -> None:
        plugin = OcrQualityPlugin()
        calc = plugin.get_calculator("confidence")
        assert isinstance(calc, ConfidenceMetricCalculator)

    def test_get_calculator_missing(self) -> None:
        plugin = OcrQualityPlugin()
        with pytest.raises(QualityCalculatorNotFoundError):
            plugin.get_calculator("nonexistent")

    def test_start_stop(self) -> None:
        plugin = OcrQualityPlugin()
        plugin.start()
        assert plugin.state == PluginState.STARTED
        plugin.stop()
        assert plugin.state == PluginState.STOPPED

    def test_service_property(self) -> None:
        plugin = OcrQualityPlugin()
        assert isinstance(plugin.service, OcrQualityService)

    def test_registry_property(self) -> None:
        plugin = OcrQualityPlugin()
        assert isinstance(plugin.registry, QualityCalculatorRegistry)

    def test_default_registrations(self) -> None:
        plugin = OcrQualityPlugin()
        names = plugin.registry.registered_names()
        assert "confidence" in names
        assert "length" in names
        assert "whitespace" in names
