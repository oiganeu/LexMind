"""Unit tests for the document processing pipeline framework."""

from dataclasses import dataclass, field

import pytest

from lexmind.pipeline import (
    BaseStage,
    Pipeline,
    PipelineContext,
    PipelineManager,
    PipelineRegistry,
    RetryPolicy,
    RetryStrategy,
    StageId,
    StageResult,
)
from lexmind.pipeline.pipeline_checkpoint import InMemoryCheckpointStore
from lexmind.pipeline.pipeline_exceptions import (
    DuplicateStageError,
    StageDependencyError,
)
from lexmind.pipeline.pipeline_executor import PipelineExecutor
from lexmind.pipeline.pipeline_stage import PipelineStage


@dataclass
class RecordingStage(BaseStage):
    """A stage that records executions and returns a success result."""

    calls: list[StageId] = field(default_factory=list)

    def execute(self, context: PipelineContext) -> StageResult:
        self.calls.append(self.id)
        context.shared[str(self.id)] = "done"
        return StageResult.ok(self.id)


@dataclass
class FlakyStage(BaseStage):
    """A stage that fails a fixed number of times before succeeding."""

    fail_times: int = 1
    attempts_seen: int = 0

    def execute(self, context: PipelineContext) -> StageResult:
        self.attempts_seen += 1
        if self.attempts_seen <= self.fail_times:
            raise RuntimeError("transient failure")
        return StageResult.ok(self.id)


@dataclass
class AlwaysFailStage(BaseStage):
    """A stage that always fails."""

    rolled_back: bool = False

    def execute(self, context: PipelineContext) -> StageResult:
        raise RuntimeError("permanent failure")

    def rollback(self, context: PipelineContext) -> None:
        self.rolled_back = True


def _context(pipeline_id: str = "p1") -> PipelineContext:
    return PipelineContext(
        workspace="ws",
        document="doc",
        pipeline_id=pipeline_id,
        document_id="doc-1",
    )


def _no_sleep(_seconds: float) -> None:
    return None


def test_pipeline_creation_uses_registered_stages() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="validate"))
    pipeline = Pipeline("test", registry)
    stages = pipeline.stages()
    assert [s.id for s in stages] == [StageId.DOCUMENT_VALIDATION]


def test_stage_registration_rejects_duplicates() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.OCR, name="ocr"))
    with pytest.raises(DuplicateStageError):
        registry.register(RecordingStage(id=StageId.OCR, name="ocr-again"))


def test_dependency_validation_detects_missing() -> None:
    registry = PipelineRegistry()
    registry.register(
        RecordingStage(
            id=StageId.PARSER,
            name="parser",
            dependencies=(StageId.OCR,),
        )
    )
    with pytest.raises(StageDependencyError):
        registry.validate_dependencies()


def test_topological_order_respects_dependencies() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.OCR, name="ocr"))
    registry.register(
        RecordingStage(
            id=StageId.PARSER,
            name="parser",
            dependencies=(StageId.OCR,),
        )
    )
    order = registry.topological_order()
    assert order.index(StageId.OCR) < order.index(StageId.PARSER)


def test_executor_runs_stages_in_order() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="v"))
    registry.register(RecordingStage(id=StageId.OCR, name="ocr"))
    pipeline = Pipeline("run", registry)
    executor = PipelineExecutor(sleep=_no_sleep)
    result = executor.execute(pipeline, _context())
    assert result.completed
    assert result.succeeded
    executed = [r.stage_id for r in result.stage_results]
    assert executed == [StageId.DOCUMENT_VALIDATION, StageId.OCR]


def test_disabled_stage_is_skipped() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.OCR, name="ocr", enabled=False))
    pipeline = Pipeline("run", registry)
    result = PipelineExecutor(sleep=_no_sleep).execute(pipeline, _context())
    ocr = result.result_for(StageId.OCR)
    assert ocr is not None
    assert ocr.status.value == "skipped"


def test_checkpoint_created_per_stage() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="v"))
    registry.register(RecordingStage(id=StageId.OCR, name="ocr"))
    store = InMemoryCheckpointStore()
    executor = PipelineExecutor(checkpoint_store=store, sleep=_no_sleep)
    executor.execute(Pipeline("run", registry), _context("cp"))
    checkpoint = store.restore("cp")
    assert checkpoint is not None
    assert StageId.OCR in checkpoint.completed_stages
    assert StageId.DOCUMENT_VALIDATION in checkpoint.completed_stages


def test_resume_skips_completed_stages() -> None:
    registry = PipelineRegistry()
    first = RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="v")
    second = RecordingStage(id=StageId.OCR, name="ocr")
    registry.register(first)
    registry.register(second)
    store = InMemoryCheckpointStore()
    executor = PipelineExecutor(checkpoint_store=store, sleep=_no_sleep)
    pipeline = Pipeline("run", registry)

    executor.execute(pipeline, _context("res"))
    first.calls.clear()
    second.calls.clear()

    result = executor.execute(pipeline, _context("res"), resume=True)
    assert first.calls == []
    assert second.calls == []
    assert result.completed


def test_retry_policy_recovers_flaky_stage() -> None:
    registry = PipelineRegistry()
    stage = FlakyStage(
        id=StageId.OCR,
        name="ocr",
        fail_times=2,
        retry_policy=RetryPolicy(
            strategy=RetryStrategy.IMMEDIATE,
            max_attempts=3,
        ),
    )
    registry.register(stage)
    result = PipelineExecutor(sleep=_no_sleep).execute(Pipeline("run", registry), _context("retry"))
    assert result.succeeded
    assert stage.attempts_seen == 3


def test_failed_stage_stops_and_rolls_back() -> None:
    registry = PipelineRegistry()
    stage = AlwaysFailStage(id=StageId.OCR, name="ocr")
    later = RecordingStage(id=StageId.PARSER, name="parser")
    registry.register(stage)
    registry.register(later)
    result = PipelineExecutor(sleep=_no_sleep).execute(Pipeline("run", registry), _context("fail"))
    assert not result.completed
    assert not result.succeeded
    assert stage.rolled_back
    assert later.calls == []


def test_metrics_track_retries_and_duration() -> None:
    registry = PipelineRegistry()
    stage = FlakyStage(
        id=StageId.OCR,
        name="ocr",
        fail_times=1,
        retry_policy=RetryPolicy(strategy=RetryStrategy.IMMEDIATE, max_attempts=2),
    )
    registry.register(stage)
    context = _context("metrics")
    PipelineExecutor(sleep=_no_sleep).execute(Pipeline("run", registry), context)
    metrics = context.statistics.metrics_for(StageId.OCR)
    assert metrics.retries == 1
    assert metrics.failures == 1
    assert context.statistics.total_retries == 1


def test_cancellation_stops_pipeline() -> None:
    registry = PipelineRegistry()
    registry.register(RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="v"))
    context = _context("cancel")
    context.cancellation_token.cancel("user requested")
    result = PipelineExecutor(sleep=_no_sleep).execute(Pipeline("run", registry), context)
    assert not result.completed


def test_manager_runs_pipeline() -> None:
    manager = PipelineManager()
    manager.register_stage(RecordingStage(id=StageId.DOCUMENT_VALIDATION, name="v"))
    pipeline = manager.create_pipeline("managed")
    result = manager.run(pipeline, _context("mgr"))
    assert result.completed


def test_base_stage_is_pipeline_stage() -> None:
    stage = BaseStage(id=StageId.COMPLETED, name="completed")
    assert isinstance(stage, PipelineStage)


def test_retry_policy_exponential_backoff() -> None:
    policy = RetryPolicy(
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_attempts=5,
        base_delay_seconds=1.0,
        multiplier=2.0,
        max_delay_seconds=10.0,
    )
    assert policy.delay_for(1) == 1.0
    assert policy.delay_for(2) == 2.0
    assert policy.delay_for(3) == 4.0
    assert policy.delay_for(10) == 10.0
    assert policy.should_retry(4) is True
    assert policy.should_retry(5) is False
