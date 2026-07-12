"""Unit tests for the OCR benchmark framework."""

from __future__ import annotations

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.benchmark.benchmark_runner import (
    BenchmarkRunnerNotFoundError,
    BenchmarkRunnerRegistry,
    DefaultBenchmarkRunner,
)
from lexmind.ocr.benchmark.benchmark_types import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkReport,
    BenchmarkResult,
)
from lexmind.ocr.benchmark.ocr_benchmark import OcrBenchmarkService
from lexmind.ocr.benchmark.ocr_benchmark_events import (
    OcrBenchmarkCompleted,
    OcrBenchmarkFailed,
    OcrBenchmarkStarted,
)
from lexmind.ocr.benchmark.ocr_benchmark_plugin import OcrBenchmarkPlugin


class _StubEngine:
    """Minimal in-memory OCR engine for tests."""

    def __init__(self, name: str = "stub", text: str = "hello world") -> None:
        self._name = name
        self._text = text

    @property
    def name(self) -> str:
        return self._name

    def recognize(self, image_ref: str) -> str:
        return self._text


class _FailingEngine:
    """Engine that raises on recognise."""

    @property
    def name(self) -> str:
        return "failing"

    def recognize(self, image_ref: str) -> str:
        raise RuntimeError("boom")


class _RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> list:
        self.events.append(event)
        return []


def _dataset() -> BenchmarkDataset:
    return BenchmarkDataset(
        name="ds",
        cases=(
            BenchmarkCase(id="c1", expected_text="hello world", image_ref="i1"),
            BenchmarkCase(id="c2", expected_text="hello world", image_ref="i2"),
        ),
    )


# --- benchmark_types -------------------------------------------------------


def test_benchmark_case_requires_id():
    with pytest.raises(ValueError):
        BenchmarkCase(id="", expected_text="x", image_ref="i")


def test_dataset_requires_name():
    with pytest.raises(ValueError):
        BenchmarkDataset(name="", cases=())


def test_dataset_case_count():
    assert _dataset().case_count == 2


def test_result_requires_engine_name():
    with pytest.raises(ValueError):
        BenchmarkResult(engine_name="", case_id="c", accuracy=0.5, latency_ms=1.0)


def test_result_requires_case_id():
    with pytest.raises(ValueError):
        BenchmarkResult(engine_name="e", case_id="", accuracy=0.5, latency_ms=1.0)


def test_result_accuracy_out_of_range_high():
    with pytest.raises(ValueError):
        BenchmarkResult(engine_name="e", case_id="c", accuracy=1.5, latency_ms=1.0)


def test_result_accuracy_out_of_range_low():
    with pytest.raises(ValueError):
        BenchmarkResult(engine_name="e", case_id="c", accuracy=-0.1, latency_ms=1.0)


def test_report_requires_names():
    with pytest.raises(ValueError):
        BenchmarkReport(engine_name="", dataset_name="d", results=())


def test_report_mean_accuracy_empty():
    report = BenchmarkReport(engine_name="e", dataset_name="d", results=())
    assert report.mean_accuracy == 0.0
    assert report.mean_latency == 0.0


def test_report_means_and_acceptance():
    report = BenchmarkReport(
        engine_name="e",
        dataset_name="d",
        results=(
            BenchmarkResult("e", "c1", 1.0, 10.0),
            BenchmarkResult("e", "c2", 0.0, 30.0),
        ),
    )
    assert report.mean_accuracy == 0.5
    assert report.mean_latency == 20.0
    assert report.is_acceptable(0.4) is True
    assert report.is_acceptable(0.6) is False


def test_report_is_acceptable_bad_threshold():
    report = BenchmarkReport(engine_name="e", dataset_name="d", results=())
    with pytest.raises(ValueError):
        report.is_acceptable(1.5)


# --- benchmark_runner ------------------------------------------------------


def test_default_runner_computes_accuracy_and_latency():
    runner = DefaultBenchmarkRunner()
    engine = _StubEngine(text="hello world")
    report = runner.run(_dataset(), engine)
    assert report.engine_name == "stub"
    assert report.dataset_name == "ds"
    assert len(report.results) == 2
    for r in report.results:
        assert r.accuracy == 1.0
        assert r.latency_ms >= 0.0


def test_default_runner_empty_expected_is_perfect():
    dataset = BenchmarkDataset(
        name="ds",
        cases=(BenchmarkCase(id="c1", expected_text="", image_ref="i1"),),
    )
    report = DefaultBenchmarkRunner().run(dataset, _StubEngine(text=""))
    assert report.mean_accuracy == 1.0


def test_default_runner_partial_match():
    dataset = BenchmarkDataset(
        name="ds",
        cases=(BenchmarkCase(id="c1", expected_text="hello world", image_ref="i1"),),
    )
    report = DefaultBenchmarkRunner().run(dataset, _StubEngine(text="hello"))
    assert 0.0 < report.mean_accuracy < 1.0


def test_default_runner_empty_actual_scores_zero():
    dataset = BenchmarkDataset(
        name="ds",
        cases=(BenchmarkCase(id="c1", expected_text="hello", image_ref="i1"),),
    )
    report = DefaultBenchmarkRunner().run(dataset, _StubEngine(text=""))
    assert report.mean_accuracy == 0.0


def test_default_runner_requires_dataset():
    with pytest.raises(ValueError):
        DefaultBenchmarkRunner().run(None, _StubEngine())  # type: ignore[arg-type]


def test_default_runner_requires_engine():
    with pytest.raises(ValueError):
        DefaultBenchmarkRunner().run(_dataset(), None)  # type: ignore[arg-type]


def test_default_runner_name_empty():
    with pytest.raises(ValueError):
        DefaultBenchmarkRunner(name="")


def test_registry_register_rejects_empty_name():
    class _Runner:
        @property
        def name(self) -> str:
            return ""

        def run(self, dataset, engine, options=None):
            return BenchmarkReport("e", "d", ())

    with pytest.raises(ValueError):
        BenchmarkRunnerRegistry().register(_Runner())


def test_registry_register_get_has():
    registry = BenchmarkRunnerRegistry()
    runner = DefaultBenchmarkRunner()
    registry.register(runner)
    assert registry.get("default") is runner
    assert registry.has("default") is True
    assert registry.has("missing") is False
    assert registry.registered_names() == ["default"]


def test_registry_get_missing_raises():
    with pytest.raises(BenchmarkRunnerNotFoundError):
        BenchmarkRunnerRegistry().get("nope")


# --- ocr_benchmark service -------------------------------------------------


def test_service_uses_default_runner():
    bus = _RecordingBus()
    service = OcrBenchmarkService(event_bus=bus)
    report = service.run_benchmark(_dataset(), _StubEngine(text="hello world"))
    assert report.engine_name == "stub"
    assert any(isinstance(e, OcrBenchmarkStarted) for e in bus.events)
    completed = [e for e in bus.events if isinstance(e, OcrBenchmarkCompleted)]
    assert completed and completed[0].mean_accuracy == 1.0


def test_service_missing_runner_raises():
    bus = _RecordingBus()
    service = OcrBenchmarkService(registry=BenchmarkRunnerRegistry(), event_bus=bus)
    with pytest.raises(BenchmarkRunnerNotFoundError):
        service.run_benchmark(_dataset(), _StubEngine())
    assert any(isinstance(e, OcrBenchmarkFailed) for e in bus.events)


def test_service_failure_emits_failed_and_reraises():
    bus = _RecordingBus()
    service = OcrBenchmarkService(event_bus=bus)
    with pytest.raises(RuntimeError):
        service.run_benchmark(_dataset(), _FailingEngine())
    failed = [e for e in bus.events if isinstance(e, OcrBenchmarkFailed)]
    assert failed and "boom" in failed[0].error_message


def test_service_no_bus_no_error():
    service = OcrBenchmarkService()
    report = service.run_benchmark(_dataset(), _StubEngine(text="hello world"))
    assert report.engine_name == "stub"


def test_service_explicit_runner_name():
    registry = BenchmarkRunnerRegistry()
    registry.register(DefaultBenchmarkRunner(name="fast"))
    service = OcrBenchmarkService(registry=registry)
    report = service.run_benchmark(
        _dataset(), _StubEngine(text="hello world"), runner_name="fast"
    )
    assert report.dataset_name == "ds"


# --- ocr_benchmark_plugin --------------------------------------------------


def test_plugin_capability_and_metadata():
    plugin = OcrBenchmarkPlugin()
    assert plugin.get_metadata().capabilities
    caps = [c.value for c in plugin.get_metadata().capabilities]
    assert "ocr_benchmark" in caps
    assert plugin.state.value == "discovered"


def test_plugin_run_benchmark_returns_report():
    plugin = OcrBenchmarkPlugin()
    report = plugin.run_benchmark(_dataset(), _StubEngine(text="hello world"))
    assert isinstance(report, BenchmarkReport)
    assert report.mean_accuracy == 1.0


def test_plugin_register_runner():
    plugin = OcrBenchmarkPlugin()
    plugin.register_runner(DefaultBenchmarkRunner(name="custom"))
    assert plugin.registry.has("custom")


def test_plugin_start_stop():
    plugin = OcrBenchmarkPlugin()
    plugin.start()
    assert plugin.state.value == "started"
    plugin.stop()
    assert plugin.state.value == "stopped"


def test_plugin_events_published():
    bus = _RecordingBus()
    plugin = OcrBenchmarkPlugin(event_bus=bus)
    plugin.run_benchmark(_dataset(), _StubEngine(text="hello world"))
    assert any(isinstance(e, OcrBenchmarkStarted) for e in bus.events)
    assert any(isinstance(e, OcrBenchmarkCompleted) for e in bus.events)
