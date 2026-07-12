"""Unit tests for the OCR pipeline framework (Task 44)."""

from __future__ import annotations

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.pipeline.ocr_pipeline import OcrPipelineService
from lexmind.ocr.pipeline.ocr_pipeline_events import (
    OcrPipelineCompleted,
    OcrPipelineFailed,
    OcrPipelineStarted,
    OcrPipelineStepCompleted,
)
from lexmind.ocr.pipeline.ocr_pipeline_plugin import OcrPipelinePlugin
from lexmind.ocr.pipeline.pipeline_step import (
    IdentityPipelineStep,
    OcrPipelineStepNotFoundError,
    OcrPipelineStepRegistry,
    PipelineContext,
)
from lexmind.ocr.pipeline.pipeline_types import (
    OcrPipelineOptions,
    OcrPipelineResult,
    PipelineStepResult,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> list[object]:  # noqa: ANN001
        self.events.append(event)
        return []


class FailingStep:
    """Step that always raises RuntimeError."""

    @property
    def name(self) -> str:
        return "failing"

    def process(self, context: PipelineContext) -> PipelineStepResult:  # noqa: ARG002
        raise RuntimeError("step exploded")


class EchoStep:
    """Step that returns the page_number in data."""

    @property
    def name(self) -> str:
        return "echo"

    def process(self, context: PipelineContext) -> PipelineStepResult:
        return PipelineStepResult(
            step_name=self.name,
            data=f"page-{context.page_number}",
            metadata={"page_number": context.page_number},
        )


class OrderedStep:
    """Step that records execution order via shared state."""

    def __init__(self, label: str) -> None:
        self._label = label

    @property
    def name(self) -> str:
        return self._label

    def process(self, context: PipelineContext) -> PipelineStepResult:
        order = context.state.setdefault("order", [])
        order.append(self._label)
        return PipelineStepResult(step_name=self.name, data=self._label)


# ---------------------------------------------------------------------------
# AC-1: Value objects
# ---------------------------------------------------------------------------


class TestPipelineStepResult:
    """PipelineStepResult validation."""

    def test_creation(self) -> None:
        result = PipelineStepResult(
            step_name="s", data="d", metadata={"k": "v"}, duration_ms=1.5
        )
        assert result.step_name == "s"
        assert result.data == "d"
        assert result.metadata == {"k": "v"}
        assert result.duration_ms == 1.5

    def test_defaults(self) -> None:
        result = PipelineStepResult(step_name="s", data=None)
        assert result.metadata == {}
        assert result.duration_ms == 0.0

    def test_frozen(self) -> None:
        result = PipelineStepResult(step_name="s", data=None)
        with pytest.raises(AttributeError):
            result.step_name = "x"  # type: ignore[misc]


class TestOcrPipelineOptions:
    """OcrPipelineOptions enabled/keeps logic."""

    def test_enabled_true(self) -> None:
        opts = OcrPipelineOptions(step_names=("a", "b"))
        assert opts.enabled("a")
        assert opts.enabled("b")

    def test_enabled_false(self) -> None:
        opts = OcrPipelineOptions(step_names=("a",))
        assert not opts.enabled("c")

    def test_keeps_alias(self) -> None:
        opts = OcrPipelineOptions(step_names=("x",))
        assert opts.keeps("x")
        assert not opts.keeps("y")

    def test_empty(self) -> None:
        opts = OcrPipelineOptions()
        assert not opts.enabled("anything")
        assert opts.step_names == ()


class TestOcrPipelineResult:
    """OcrPipelineResult properties."""

    def test_step_count(self) -> None:
        r1 = PipelineStepResult(step_name="a", data=None)
        r2 = PipelineStepResult(step_name="b", data=None)
        result = OcrPipelineResult(page_number=1, step_results=(r1, r2))
        assert result.step_count == 2
        assert result.is_success

    def test_defaults(self) -> None:
        result = OcrPipelineResult(page_number=3)
        assert result.step_count == 0
        assert result.is_success
        assert result.final_text == ""
        assert result.duration_ms == 0.0


# ---------------------------------------------------------------------------
# AC-2: PipelineContext and IdentityPipelineStep
# ---------------------------------------------------------------------------


class TestPipelineContext:
    """PipelineContext validation."""

    def test_defaults(self) -> None:
        ctx = PipelineContext(image_data=b"img")
        assert ctx.page_number == 1
        assert ctx.state == {}

    def test_custom_page_number(self) -> None:
        ctx = PipelineContext(image_data=b"img", page_number=5)
        assert ctx.page_number == 5

    def test_state_mutation(self) -> None:
        ctx = PipelineContext(image_data=b"img")
        ctx.state["key"] = "val"
        assert ctx.state["key"] == "val"

    def test_frozen(self) -> None:
        ctx = PipelineContext(image_data=b"img")
        with pytest.raises(AttributeError):
            ctx.image_data = b"x"  # type: ignore[misc]


class TestIdentityPipelineStep:
    """IdentityPipelineStep passthrough behaviour."""

    def test_name(self) -> None:
        step = IdentityPipelineStep()
        assert step.name == "identity"

    def test_process_copies_image_data(self) -> None:
        step = IdentityPipelineStep()
        ctx = PipelineContext(image_data=b"hello")
        result = step.process(ctx)
        assert result.data == b"hello"
        assert result.step_name == "identity"
        assert result.metadata["bytes"] == 5

    def test_process_decodes_text(self) -> None:
        step = IdentityPipelineStep()
        ctx = PipelineContext(image_data=b"test text")
        result = step.process(ctx)
        assert result.metadata["text"] == "test text"

    def test_process_handles_non_utf8(self) -> None:
        step = IdentityPipelineStep()
        ctx = PipelineContext(image_data=b"\xff\xfe")
        result = step.process(ctx)
        assert isinstance(result.metadata["text"], str)


# ---------------------------------------------------------------------------
# AC-2: Step registry
# ---------------------------------------------------------------------------


class TestOcrPipelineStepRegistry:
    """Registry register/get/has/registered_names."""

    def test_register_and_get(self) -> None:
        registry = OcrPipelineStepRegistry()
        step = IdentityPipelineStep()
        registry.register(step)
        assert registry.has("identity")
        assert registry.get("identity") is step

    def test_register_empty_name_raises(self) -> None:
        registry = OcrPipelineStepRegistry()

        class EmptyNameStep:
            @property
            def name(self) -> str:
                return ""

            def process(self, context: PipelineContext) -> PipelineStepResult:
                return PipelineStepResult(step_name="", data=None)

        with pytest.raises(ValueError, match="must not be empty"):
            registry.register(EmptyNameStep())

    def test_get_missing_raises(self) -> None:
        registry = OcrPipelineStepRegistry()
        with pytest.raises(OcrPipelineStepNotFoundError):
            registry.get("nonexistent")

    def test_registered_names_sorted(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(OrderedStep("z"))
        registry.register(OrderedStep("a"))
        registry.register(OrderedStep("m"))
        assert registry.registered_names() == ["a", "m", "z"]

    def test_has_false_for_unknown(self) -> None:
        registry = OcrPipelineStepRegistry()
        assert not registry.has("nope")


# ---------------------------------------------------------------------------
# AC-3: Service orchestration
# ---------------------------------------------------------------------------


class TestOcrPipelineService:
    """Service runs steps, emits events, handles errors."""

    def test_run_default_identity(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(IdentityPipelineStep())
        service = OcrPipelineService(registry)
        result = service.run(b"hello")
        assert result.is_success
        assert result.step_count == 1
        assert result.step_results[0].step_name == "identity"

    def test_run_custom_options(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(EchoStep())
        service = OcrPipelineService(registry, default_sequence=("identity",))
        opts = OcrPipelineOptions(step_names=("echo",))
        result = service.run(b"img", options=opts, page_number=7)
        assert result.step_count == 1
        assert result.final_text == "page-7"

    def test_steps_run_in_order(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(OrderedStep("first"))
        registry.register(OrderedStep("second"))
        registry.register(OrderedStep("third"))
        service = OcrPipelineService(registry)
        opts = OcrPipelineOptions(step_names=("third", "first", "second"))
        result = service.run(b"img", options=opts)
        assert result.is_success
        # Check the step names are in the declared order
        names = [sr.step_name for sr in result.step_results]
        assert names == ["third", "first", "second"]

    def test_empty_image_raises(self) -> None:
        registry = OcrPipelineStepRegistry()
        service = OcrPipelineService(registry)
        with pytest.raises(ValueError, match="empty"):
            service.run(b"")

    def test_missing_step_raises(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(IdentityPipelineStep())
        service = OcrPipelineService(registry)
        opts = OcrPipelineOptions(step_names=("identity", "nonexistent"))
        with pytest.raises(OcrPipelineStepNotFoundError):
            service.run(b"img", options=opts)

    def test_events_started_and_completed(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(IdentityPipelineStep())
        bus = RecordingBus()
        service = OcrPipelineService(registry, event_bus=bus)
        service.run(b"img", page_number=3)
        started = [e for e in bus.events if isinstance(e, OcrPipelineStarted)]
        completed = [e for e in bus.events if isinstance(e, OcrPipelineCompleted)]
        step_completed = [
            e for e in bus.events if isinstance(e, OcrPipelineStepCompleted)
        ]
        assert len(started) == 1
        assert started[0].page_number == 3
        assert started[0].step_names == ("identity",)
        assert len(completed) == 1
        assert completed[0].step_count == 1
        assert completed[0].page_number == 3
        assert len(step_completed) == 1
        assert step_completed[0].step_name == "identity"

    def test_failing_step_emits_failed_and_stops(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(FailingStep())
        registry.register(IdentityPipelineStep())
        bus = RecordingBus()
        service = OcrPipelineService(registry, event_bus=bus)
        with pytest.raises(RuntimeError, match="step exploded"):
            service.run(
                b"img",
                options=OcrPipelineOptions(step_names=("failing", "identity")),
            )
        failed = [e for e in bus.events if isinstance(e, OcrPipelineFailed)]
        assert len(failed) == 1
        assert failed[0].step_name == "failing"
        assert "step exploded" in failed[0].error_message
        # Completed should NOT have been emitted
        completed = [e for e in bus.events if isinstance(e, OcrPipelineCompleted)]
        assert len(completed) == 0
        # StepCompleted for the failing step should NOT have been emitted
        step_completed = [
            e for e in bus.events if isinstance(e, OcrPipelineStepCompleted)
        ]
        assert len(step_completed) == 0

    def test_no_event_bus_still_works(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(IdentityPipelineStep())
        service = OcrPipelineService(registry)
        result = service.run(b"img")
        assert result.is_success

    def test_multiple_steps_collect_results(self) -> None:
        registry = OcrPipelineStepRegistry()
        registry.register(IdentityPipelineStep())
        registry.register(EchoStep())
        service = OcrPipelineService(registry)
        opts = OcrPipelineOptions(step_names=("identity", "echo"))
        result = service.run(b"img", options=opts, page_number=2)
        assert result.step_count == 2
        assert result.step_results[0].step_name == "identity"
        assert result.step_results[1].step_name == "echo"
        assert result.final_text == "page-2"


# ---------------------------------------------------------------------------
# AC-4: Plugin integration
# ---------------------------------------------------------------------------


class TestOcrPipelinePlugin:
    """Plugin capability, run, register_step, start/stop."""

    def test_capability(self) -> None:
        plugin = OcrPipelinePlugin()
        assert PluginCapability.OCR_PIPELINE in plugin.get_metadata().capabilities

    def test_default_identity_step(self) -> None:
        plugin = OcrPipelinePlugin()
        assert plugin.registry.has("identity")

    def test_run_returns_result(self) -> None:
        plugin = OcrPipelinePlugin()
        result = plugin.run(b"hello world")
        assert isinstance(result, OcrPipelineResult)
        assert result.is_success
        assert result.step_count == 1

    def test_register_step(self) -> None:
        plugin = OcrPipelinePlugin()
        plugin.register_step(EchoStep())
        assert plugin.registry.has("echo")
        result = plugin.run(
            b"img",
            options=OcrPipelineOptions(step_names=("identity", "echo")),
            page_number=4,
        )
        assert result.step_count == 2

    def test_start_stop(self) -> None:
        plugin = OcrPipelinePlugin()
        plugin.start()
        assert plugin.state == PluginState.STARTED
        plugin.stop()
        assert plugin.state == PluginState.STOPPED

    def test_service_property(self) -> None:
        plugin = OcrPipelinePlugin()
        assert isinstance(plugin.service, OcrPipelineService)

    def test_custom_event_bus(self) -> None:
        bus = RecordingBus()
        plugin = OcrPipelinePlugin(event_bus=bus)
        plugin.run(b"img")
        assert any(isinstance(e, OcrPipelineCompleted) for e in bus.events)

    def test_custom_default_sequence(self) -> None:
        plugin = OcrPipelinePlugin(default_sequence=("identity",))
        result = plugin.run(b"img")
        assert result.is_success


# ---------------------------------------------------------------------------
# AC-5: OcrPipelineStepNotFoundError inherits ValueError
# ---------------------------------------------------------------------------


class TestStepNotFoundError:
    """OcrPipelineStepNotFoundError is a ValueError."""

    def test_is_value_error(self) -> None:
        assert issubclass(OcrPipelineStepNotFoundError, ValueError)

    def test_can_be_caught_as_value_error(self) -> None:
        with pytest.raises(ValueError):
            raise OcrPipelineStepNotFoundError("missing")
