"""Pipeline exceptions."""

from lexmind.exceptions import LexMindError


class PipelineError(LexMindError):
    """Base class for pipeline errors."""


class StageNotFoundError(PipelineError):
    """Raised when a referenced stage is not registered."""


class DuplicateStageError(PipelineError):
    """Raised when a stage id is registered more than once."""


class StageDependencyError(PipelineError):
    """Raised when stage dependencies are missing or form a cycle."""


class StageExecutionError(PipelineError):
    """Raised when a stage fails and retries are exhausted."""


class StageTimeoutError(PipelineError):
    """Raised when a stage exceeds its timeout."""


class CheckpointError(PipelineError):
    """Raised when a checkpoint cannot be saved or restored."""


class PipelineCancelledError(PipelineError):
    """Raised when execution is cancelled."""
