"""Document processing pipeline framework.

Orchestration only: stage declarations, execution, checkpointing, retries,
metrics, and events. No OCR, parsing, embeddings, or indexing logic lives
here — those are provided by later tasks as stage implementations.
"""

from lexmind.pipeline.pipeline import Pipeline
from lexmind.pipeline.pipeline_checkpoint import (
    Checkpoint,
    CheckpointStore,
    InMemoryCheckpointStore,
)
from lexmind.pipeline.pipeline_context import CancellationToken, PipelineContext
from lexmind.pipeline.pipeline_exceptions import (
    CheckpointError,
    DuplicateStageError,
    PipelineCancelledError,
    PipelineError,
    StageDependencyError,
    StageExecutionError,
    StageNotFoundError,
    StageTimeoutError,
)
from lexmind.pipeline.pipeline_executor import PipelineExecutor
from lexmind.pipeline.pipeline_manager import PipelineManager
from lexmind.pipeline.pipeline_registry import PipelineRegistry
from lexmind.pipeline.pipeline_result import PipelineResult, StageResult
from lexmind.pipeline.pipeline_retry import NO_RETRY, RetryPolicy, RetryStrategy
from lexmind.pipeline.pipeline_stage import (
    PIPELINE_STAGE_ORDER,
    BaseStage,
    PipelineStage,
    StageId,
    StageStatus,
)
from lexmind.pipeline.pipeline_statistics import PipelineStatistics, StageMetrics

__all__ = [
    "NO_RETRY",
    "PIPELINE_STAGE_ORDER",
    "BaseStage",
    "CancellationToken",
    "Checkpoint",
    "CheckpointError",
    "CheckpointStore",
    "DuplicateStageError",
    "InMemoryCheckpointStore",
    "Pipeline",
    "PipelineCancelledError",
    "PipelineContext",
    "PipelineError",
    "PipelineExecutor",
    "PipelineManager",
    "PipelineRegistry",
    "PipelineResult",
    "PipelineStage",
    "PipelineStatistics",
    "RetryPolicy",
    "RetryStrategy",
    "StageDependencyError",
    "StageExecutionError",
    "StageId",
    "StageMetrics",
    "StageNotFoundError",
    "StageResult",
    "StageStatus",
    "StageTimeoutError",
]
