"""Ingestion job model and lifecycle states."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class JobState(StrEnum):
    """Lifecycle states of an ingestion job."""

    CREATED = "created"
    DISCOVERING = "discovering"
    VALIDATING = "validating"
    IMPORTING = "importing"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


# Allowed forward transitions between job states.
_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.CREATED: frozenset({JobState.DISCOVERING, JobState.CANCELLED, JobState.FAILED}),
    JobState.DISCOVERING: frozenset(
        {JobState.VALIDATING, JobState.PAUSED, JobState.CANCELLED, JobState.FAILED}
    ),
    JobState.VALIDATING: frozenset(
        {JobState.IMPORTING, JobState.PAUSED, JobState.CANCELLED, JobState.FAILED}
    ),
    JobState.IMPORTING: frozenset(
        {JobState.COMPLETED, JobState.PAUSED, JobState.CANCELLED, JobState.FAILED}
    ),
    JobState.PAUSED: frozenset(
        {JobState.DISCOVERING, JobState.VALIDATING, JobState.IMPORTING, JobState.CANCELLED}
    ),
    JobState.CANCELLED: frozenset(),
    JobState.COMPLETED: frozenset(),
    JobState.FAILED: frozenset(),
}


def can_transition(current: JobState, target: JobState) -> bool:
    """Return True if the job may move from ``current`` to ``target``."""
    return target in _TRANSITIONS[current]


@dataclass
class IngestionJob:
    """A single ingestion job tracking the import of a source."""

    workspace_id: str
    source: str
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: JobState = JobState.CREATED
    start_time: datetime | None = None
    end_time: datetime | None = None
    progress: float = 0.0
    files_processed: int = 0
    files_failed: int = 0
    warnings: list[str] = field(default_factory=list)

    def transition_to(self, target: JobState) -> None:
        """Move the job to ``target`` if the transition is allowed."""
        from lexmind.ingestion.ingestion_exceptions import InvalidJobStateError

        if not can_transition(self.state, target):
            raise InvalidJobStateError(
                f"Cannot transition job '{self.job_id}' from {self.state} to {target}."
            )
        if target == JobState.DISCOVERING and self.start_time is None:
            self.start_time = datetime.now(UTC)
        if target in (JobState.COMPLETED, JobState.CANCELLED, JobState.FAILED):
            self.end_time = datetime.now(UTC)
        self.state = target

    @property
    def is_terminal(self) -> bool:
        """Return True if the job has reached a terminal state."""
        return self.state in (JobState.COMPLETED, JobState.CANCELLED, JobState.FAILED)

    def add_warning(self, message: str) -> None:
        """Record a non-fatal warning for the job."""
        self.warnings.append(message)
