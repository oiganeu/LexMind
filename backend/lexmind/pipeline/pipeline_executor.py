"""Pipeline executor.

Runs a pipeline's stages sequentially with dependency validation,
conditional skipping, retries, checkpointing, metrics, and event
publishing. Parallel execution is reserved for a future task.
"""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from lexmind.pipeline import pipeline_events as events
from lexmind.pipeline.pipeline import Pipeline
from lexmind.pipeline.pipeline_checkpoint import (
    Checkpoint,
    CheckpointStore,
    InMemoryCheckpointStore,
)
from lexmind.pipeline.pipeline_context import PipelineContext
from lexmind.pipeline.pipeline_exceptions import PipelineCancelledError
from lexmind.pipeline.pipeline_result import PipelineResult, StageResult
from lexmind.pipeline.pipeline_stage import PipelineStage

EmitFn = Callable[[str, dict[str, Any]], None]


class PipelineExecutor:
    """Executes pipelines sequentially with checkpoints and retries."""

    def __init__(
        self,
        checkpoint_store: CheckpointStore | None = None,
        emit: EmitFn | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._checkpoints: CheckpointStore = checkpoint_store or InMemoryCheckpointStore()
        self._emit = emit or (lambda name, payload: None)
        self._sleep = sleep

    @property
    def checkpoints(self) -> CheckpointStore:
        """Return the checkpoint store used by the executor."""
        return self._checkpoints

    def execute(
        self,
        pipeline: Pipeline,
        context: PipelineContext,
        resume: bool = False,
    ) -> PipelineResult:
        """Run a pipeline against a context and return the aggregate result."""
        pipeline.validate()
        result = PipelineResult(
            pipeline_id=context.pipeline_id,
            document_id=context.document_id,
        )
        context.statistics.start()

        checkpoint = self._initial_checkpoint(context, resume)
        completed = set(checkpoint.completed_stages)
        self._emit(events.PIPELINE_STARTED, {"pipeline_id": context.pipeline_id})

        try:
            for stage in pipeline.stages():
                if stage.id in completed:
                    result.add(StageResult.skipped(stage.id, "already completed"))
                    continue

                self._raise_if_cancelled(context)

                if not stage.validate(context):
                    context.statistics.mark_skipped(stage.id)
                    result.add(StageResult.skipped(stage.id, "validate() returned False"))
                    continue

                stage_result = self._run_stage(stage, context)
                result.add(stage_result)

                if not stage_result.success:
                    self._rollback(stage, context)
                    self._emit(
                        events.PIPELINE_FAILED,
                        {"pipeline_id": context.pipeline_id, "stage": stage.id},
                    )
                    return result

                checkpoint = checkpoint.with_stage(stage.id, context.shared)
                self._checkpoints.save(checkpoint)
                self._emit(events.CHECKPOINT_CREATED, {"stage": stage.id})
        except PipelineCancelledError:
            self._emit(events.PIPELINE_CANCELLED, {"pipeline_id": context.pipeline_id})
            return result
        finally:
            context.statistics.finish()

        result.completed = True
        self._emit(events.PIPELINE_COMPLETED, {"pipeline_id": context.pipeline_id})
        return result

    def _initial_checkpoint(self, context: PipelineContext, resume: bool) -> Checkpoint:
        if resume:
            existing = self._checkpoints.restore(context.pipeline_id)
            if existing is not None:
                context.shared.update(existing.shared)
                return existing
        return Checkpoint(
            pipeline_id=context.pipeline_id,
            document_id=context.document_id,
        )

    def _run_stage(self, stage: PipelineStage, context: PipelineContext) -> StageResult:
        metrics = context.statistics.metrics_for(stage.id)
        policy = stage.retry_policy
        attempt = 0
        last_error = "unknown error"

        while True:
            attempt += 1
            self._emit(events.STAGE_STARTED, {"stage": stage.id, "attempt": attempt})
            metrics.start_time = datetime.now(UTC)
            started = time.perf_counter()
            try:
                stage_result = stage.execute(context)
                elapsed = time.perf_counter() - started
                metrics.end_time = datetime.now(UTC)
                metrics.cpu_time_seconds = elapsed
                stage_result.attempts = attempt
                stage_result.execution_time_seconds = elapsed
                if stage_result.success:
                    self._emit(events.STAGE_COMPLETED, {"stage": stage.id})
                    return stage_result
                last_error = "; ".join(stage_result.errors) or "stage reported failure"
            except Exception as exc:  # noqa: BLE001 - retries wrap any stage error
                metrics.end_time = datetime.now(UTC)
                last_error = str(exc)

            metrics.failures += 1
            self._emit(
                events.STAGE_FAILED,
                {"stage": stage.id, "attempt": attempt, "error": last_error},
            )
            if not policy.should_retry(attempt):
                failed = StageResult.failed(stage.id, last_error)
                failed.attempts = attempt
                return failed
            metrics.retries += 1
            delay = policy.delay_for(attempt + 1)
            if delay > 0:
                self._sleep(delay)

    def _rollback(self, stage: PipelineStage, context: PipelineContext) -> None:
        try:
            stage.rollback(context)
        except Exception:  # noqa: BLE001 - rollback must not mask original failure
            return

    def _raise_if_cancelled(self, context: PipelineContext) -> None:
        if context.is_cancelled:
            raise PipelineCancelledError(context.cancellation_token.reason or "pipeline cancelled")
