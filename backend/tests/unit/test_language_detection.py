"""Unit tests for the language detection framework (Task 40)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.language_detection.language_detection import LanguageDetectionService
from lexmind.language_detection.language_detection_events import (
    LanguageDetectionCompleted,
    LanguageDetectionFailed,
    LanguageDetectionStarted,
)
from lexmind.language_detection.language_detection_plugin import (
    LanguageDetectionPlugin,
)
from lexmind.language_detection.language_detection_types import (
    DetectedLanguage,
    LanguageDetectionOptions,
    LanguageDetectionResult,
)
from lexmind.language_detection.language_detector import (
    DetectionLanguageDetector,
    LanguageDetectorNotFoundError,
    LanguageDetectorRegistry,
    RuleBasedLanguageDetector,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState

# ---------------------------------------------------------------------------
# Type validation tests
# ---------------------------------------------------------------------------


def test_detected_language_validation() -> None:
    """DetectedLanguage rejects empty code and out-of-range confidence."""
    with pytest.raises(ValueError, match="code must not be empty"):
        DetectedLanguage(code="", confidence=0.9)
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        DetectedLanguage(code="en", confidence=1.5)
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        DetectedLanguage(code="en", confidence=-0.1)


def test_detected_language_valid_construction() -> None:
    lang = DetectedLanguage(code="ro", confidence=0.85)
    assert lang.code == "ro"
    assert lang.confidence == 0.85


def test_options_validation() -> None:
    with pytest.raises(ValueError, match="min_confidence must be between 0 and 1"):
        LanguageDetectionOptions(min_confidence=2.0)


def test_options_keeps_filters_by_confidence() -> None:
    opts = LanguageDetectionOptions(min_confidence=0.5)
    assert opts.keeps(DetectedLanguage(code="en", confidence=0.9))
    assert not opts.keeps(DetectedLanguage(code="en", confidence=0.3))


def test_options_keeps_filters_by_candidate_codes() -> None:
    opts = LanguageDetectionOptions(candidate_codes=("ro", "de"))
    assert opts.keeps(DetectedLanguage(code="ro", confidence=0.9))
    assert not opts.keeps(DetectedLanguage(code="en", confidence=0.9))


def test_options_keeps_combined_filters() -> None:
    opts = LanguageDetectionOptions(candidate_codes=("ro",), min_confidence=0.5)
    assert opts.keeps(DetectedLanguage(code="ro", confidence=0.8))
    assert not opts.keeps(DetectedLanguage(code="ro", confidence=0.3))
    assert not opts.keeps(DetectedLanguage(code="en", confidence=0.9))


def test_result_top_language_and_is_empty() -> None:
    empty = LanguageDetectionResult(text_or_page="x")
    assert empty.is_empty
    assert empty.top_language is None

    result = LanguageDetectionResult(
        text_or_page="hello",
        languages=(
            DetectedLanguage(code="en", confidence=0.6),
            DetectedLanguage(code="ro", confidence=0.9),
        ),
        detector="test",
    )
    assert not result.is_empty
    assert result.top_language is not None
    assert result.top_language.code == "ro"


# ---------------------------------------------------------------------------
# Rule-based detector tests
# ---------------------------------------------------------------------------


def test_rule_based_detector_returns_result() -> None:
    det = RuleBasedLanguageDetector()
    assert det.name == "rule-based"
    result = det.detect("Hello, world!")
    assert isinstance(result, LanguageDetectionResult)
    assert len(result.languages) == 1
    assert result.languages[0].code == "en"
    assert result.languages[0].confidence == 1.0
    assert result.detector == "rule-based"


def test_rule_based_detector_empty_input_raises() -> None:
    det = RuleBasedLanguageDetector()
    with pytest.raises(ValueError, match="text must not be empty"):
        det.detect("")


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


def test_registry_register_get_has_names() -> None:
    registry = LanguageDetectorRegistry()
    det = RuleBasedLanguageDetector()
    registry.register(det)
    assert registry.has("rule-based")
    assert registry.get("rule-based") is det
    assert "rule-based" in registry.registered_names()


def test_registry_rejects_empty_name() -> None:
    registry = LanguageDetectorRegistry()

    class NoNameDetector:
        @property
        def name(self) -> str:
            return ""

        def detect(self, text, options=None):
            pass

    with pytest.raises(ValueError, match="detector name must not be empty"):
        registry.register(NoNameDetector())


def test_registry_missing_raises() -> None:
    registry = LanguageDetectorRegistry()
    with pytest.raises(LanguageDetectorNotFoundError):
        registry.get("nonexistent")


# ---------------------------------------------------------------------------
# DetectionLanguageDetector with stub engine
# ---------------------------------------------------------------------------


@dataclass
class StubEngine:
    """Fake language detection engine."""

    languages: tuple[DetectedLanguage, ...]

    def detect(self, text: str, options: LanguageDetectionOptions) -> tuple[DetectedLanguage, ...]:
        return self.languages


def test_detection_detector_wraps_engine() -> None:
    engine = StubEngine(
        languages=(
            DetectedLanguage(code="en", confidence=0.9),
            DetectedLanguage(code="ro", confidence=0.2),
        )
    )
    det = DetectionLanguageDetector(engine, name="stub")
    assert det.name == "stub"
    result = det.detect("Hello")
    assert len(result.languages) == 2


def test_detection_detector_filters_by_options() -> None:
    engine = StubEngine(
        languages=(
            DetectedLanguage(code="en", confidence=0.9),
            DetectedLanguage(code="ro", confidence=0.2),
        )
    )
    det = DetectionLanguageDetector(engine)
    opts = LanguageDetectionOptions(min_confidence=0.5)
    result = det.detect("Hello", options=opts)
    assert len(result.languages) == 1
    assert result.languages[0].code == "en"


def test_detection_detector_empty_input_raises() -> None:
    engine = StubEngine(languages=())
    det = DetectionLanguageDetector(engine)
    with pytest.raises(ValueError, match="text must not be empty"):
        det.detect("")


def test_detection_detector_none_engine_raises() -> None:
    with pytest.raises(ValueError, match="engine must not be None"):
        DetectionLanguageDetector(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_service_emits_started_and_completed() -> None:
    registry = LanguageDetectorRegistry()
    registry.register(RuleBasedLanguageDetector())
    bus = RecordingBus()
    service = LanguageDetectionService(registry, event_bus=bus)
    result = service.detect("Hello, world!")
    assert isinstance(result, LanguageDetectionResult)
    started = [e for e in bus.events if isinstance(e, LanguageDetectionStarted)]
    completed = [e for e in bus.events if isinstance(e, LanguageDetectionCompleted)]
    assert len(started) == 1
    assert len(completed) == 1
    assert completed[0].language_count == 1
    assert completed[0].detector == "rule-based"


def test_service_uses_explicit_detector_name() -> None:
    registry = LanguageDetectorRegistry()
    registry.register(RuleBasedLanguageDetector())
    bus = RecordingBus()
    service = LanguageDetectionService(registry, event_bus=bus)
    result = service.detect("Hello", detector_name="rule-based")
    assert result.detector == "rule-based"


def test_service_missing_detector_raises() -> None:
    bus = RecordingBus()
    service = LanguageDetectionService(LanguageDetectorRegistry(), event_bus=bus)
    with pytest.raises(LanguageDetectorNotFoundError):
        service.detect("Hello")


def test_service_failure_emits_failed_and_raises() -> None:
    class BrokenDetector:
        @property
        def name(self) -> str:
            return "broken"

        def detect(self, text, options=None):
            raise RuntimeError("boom")

    registry = LanguageDetectorRegistry()
    registry.register(BrokenDetector())  # type: ignore[arg-type]
    bus = RecordingBus()
    service = LanguageDetectionService(registry, event_bus=bus)
    with pytest.raises(RuntimeError, match="boom"):
        service.detect("Hello")
    failed = [e for e in bus.events if isinstance(e, LanguageDetectionFailed)]
    assert len(failed) == 1
    assert "boom" in failed[0].error_message


def test_service_empty_text_raises() -> None:
    registry = LanguageDetectorRegistry()
    registry.register(RuleBasedLanguageDetector())
    service = LanguageDetectionService(registry)
    with pytest.raises(ValueError, match="text must not be empty"):
        service.detect("")


def test_service_default_detector_from_registry() -> None:
    registry = LanguageDetectorRegistry()
    registry.register(RuleBasedLanguageDetector())
    service = LanguageDetectionService(registry, default_detector="rule-based")
    result = service.detect("Test")
    assert result.detector == "rule-based"


def test_service_no_event_bus_still_works() -> None:
    registry = LanguageDetectorRegistry()
    registry.register(RuleBasedLanguageDetector())
    service = LanguageDetectionService(registry, event_bus=None)
    result = service.detect("Test")
    assert not result.is_empty


# ---------------------------------------------------------------------------
# Plugin tests
# ---------------------------------------------------------------------------


def test_plugin_declares_capability() -> None:
    plugin = LanguageDetectionPlugin()
    assert PluginCapability.LANGUAGE_DETECTION in plugin.get_metadata().capabilities


def test_plugin_detect_returns_result() -> None:
    plugin = LanguageDetectionPlugin()
    result = plugin.detect("Hello, world!")
    assert isinstance(result, LanguageDetectionResult)
    assert not result.is_empty


def test_plugin_register_detector() -> None:
    plugin = LanguageDetectionPlugin()
    extra = RuleBasedLanguageDetector()
    plugin.register_detector(extra)
    assert plugin.registry.has("rule-based")


def test_plugin_start_stop() -> None:
    plugin = LanguageDetectionPlugin()
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED


def test_plugin_service_property() -> None:
    plugin = LanguageDetectionPlugin()
    assert plugin.service is plugin._service
    assert plugin.registry is plugin._service.registry
