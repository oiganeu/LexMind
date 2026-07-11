"""Pipeline manager.

Single entry point for building and running document processing
pipelines. Wires the registry, executor, checkpoint store, and EventBus,
and exposes convenience methods for creation, execution, resume, and
cancellation.
"""

from typing import Any

from lexmind.events.event import Event
from lexmind.events.event_bus import EventBus
from lexmind.pipeline.pipeline import Pipeline
from lexmind.pipeline.pipeline_checkpoint import CheckpointStore, InMemoryCheckpointStore
from lexmind.pipeline.pipeline_context import PipelineContext
from lexmind.pipeline.pipeline_executor import PipelineExecutor
from lexmind.pipeline.pipeline_registry import PipelineRegistry
from lexmind.pipeline.pipeline_result import PipelineResult
from lexmind.pipeline.pipeline_stage import PipelineStage, StageId


class PipelineManager:
    """Creates and runs pipelines over a shared registry and executor."""

    def __init__(
        self,
        registry: PipelineRegistry | None = None,
        checkpoint_store: CheckpointStore | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._registry = registry or PipelineRegistry()
        self._checkpoints = checkpoint_store or InMemoryCheckpointStore()
        self._event_bus = event_bus
        self._executor = PipelineExecutor(
            checkpoint_store=self._checkpoints,
            emit=self._emit,
        )

    @property
    def registry(self) -> PipelineRegistry:
        """Return the shared stage registry."""
        return self._registry

    @property
    def executor(self) -> PipelineExecutor:
        """Return the executor used to run pipelines."""
        return self._executor

    def register_stage(self, stage: PipelineStage) -> None:
        """Register a stage in the shared registry."""
        self._registry.register(stage)

    def create_pipeline(
        self,
        name: str,
        stage_order: tuple[StageId, ...] | None = None,
    ) -> Pipeline:
        """Create a pipeline backed by the shared registry."""
        return Pipeline(name=name, registry=self._registry, stage_order=stage_order)

    def run(self, pipeline: Pipeline, context: PipelineContext) -> PipelineResult:
        """Run a pipeline from the start."""
        return self._executor.execute(pipeline, context, resume=False)

    def resume(self, pipeline: Pipeline, context: PipelineContext) -> PipelineResult:
        """Resume a pipeline from its latest checkpoint."""
        return self._executor.execute(pipeline, context, resume=True)

    def cancel(self, context: PipelineContext, reason: str | None = None) -> None:
        """Request cancellation of an in-flight run via its context."""
        context.cancellation_token.cancel(reason)

    def _emit(self, name: str, payload: dict[str, Any]) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(Event(name=name, source_module="pipeline", payload=payload))
