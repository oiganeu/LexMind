"""Pipeline checkpointing.

A checkpoint records the completed stages and shared state of a run so
execution can resume after interruption. Storage is abstracted behind a
protocol; an in-memory implementation is provided for the framework.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from lexmind.pipeline.pipeline_exceptions import CheckpointError
from lexmind.pipeline.pipeline_stage import StageId


@dataclass
class Checkpoint:
    """Immutable snapshot of pipeline progress after a stage."""

    pipeline_id: str
    document_id: str
    completed_stages: tuple[StageId, ...] = ()
    last_stage: StageId | None = None
    shared: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_stage(self, stage_id: StageId, shared: dict[str, Any]) -> "Checkpoint":
        """Return a new checkpoint advanced by one completed stage."""
        if stage_id in self.completed_stages:
            completed = self.completed_stages
        else:
            completed = (*self.completed_stages, stage_id)
        return Checkpoint(
            pipeline_id=self.pipeline_id,
            document_id=self.document_id,
            completed_stages=completed,
            last_stage=stage_id,
            shared=dict(shared),
        )


@runtime_checkable
class CheckpointStore(Protocol):
    """Persistence contract for checkpoints."""

    def save(self, checkpoint: Checkpoint) -> None:
        """Persist a checkpoint for its pipeline."""
        ...

    def restore(self, pipeline_id: str) -> Checkpoint | None:
        """Return the latest checkpoint for a pipeline, if any."""
        ...

    def reset(self, pipeline_id: str) -> None:
        """Remove any checkpoint for a pipeline."""
        ...


class InMemoryCheckpointStore:
    """In-memory checkpoint store used by the default manager."""

    def __init__(self) -> None:
        self._store: dict[str, Checkpoint] = {}

    def save(self, checkpoint: Checkpoint) -> None:
        """Persist a checkpoint keyed by pipeline id."""
        self._store[checkpoint.pipeline_id] = checkpoint

    def restore(self, pipeline_id: str) -> Checkpoint | None:
        """Return the stored checkpoint for a pipeline, if any."""
        return self._store.get(pipeline_id)

    def resume(self, pipeline_id: str) -> Checkpoint:
        """Return the checkpoint to resume from or raise if none exists."""
        checkpoint = self._store.get(pipeline_id)
        if checkpoint is None:
            raise CheckpointError(f"No checkpoint to resume for '{pipeline_id}'")
        return checkpoint

    def reset(self, pipeline_id: str) -> None:
        """Remove any checkpoint for a pipeline."""
        self._store.pop(pipeline_id, None)
