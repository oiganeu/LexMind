"""Job domain entity -- tracks pipeline execution state."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class JobStatus(StrEnum):
    """Lifecycle states of a pipeline job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_VALID_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.PENDING: frozenset({JobStatus.RUNNING, JobStatus.CANCELLED}),
    JobStatus.RUNNING: frozenset(
        {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset({JobStatus.PENDING}),
    JobStatus.CANCELLED: frozenset(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    """Return True if the job may move from *current* to *target*."""
    return target in _VALID_TRANSITIONS[current]


@dataclass
class Job:
    """Pipeline job entity.

    Tracks the lifecycle of a single pipeline execution attempt.
    """

    workspace_id: str = ""
    job_type: str = "pipeline"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    payload: dict[str, str] = field(default_factory=dict)
    result: str = ""
    error_message: str = ""
    attempts: int = 0
    max_retries: int = 3
    priority: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("Job must belong to a workspace")

    def transition_to(self, target: JobStatus) -> None:
        """Validate and apply a state transition."""
        if not can_transition(self.status, target):
            raise ValueError(
                f"Cannot transition job from {self.status} to {target}"
            )
        now = datetime.now(UTC)
        if target == JobStatus.RUNNING and self.started_at is None:
            self.started_at = now
            self.attempts += 1
        if target in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            self.completed_at = now
        self.status = target
        self.updated_at = now

    @property
    def is_terminal(self) -> bool:
        """Return True if the job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.CANCELLED,
        )

    @property
    def can_retry(self) -> bool:
        """Return True if the job can be retried."""
        return (
            self.status == JobStatus.FAILED
            and self.attempts < self.max_retries
        )

    def retry(self) -> None:
        """Reset to PENDING for retry."""
        if not self.can_retry:
            raise ValueError(
                f"Job cannot be retried: status={self.status}, "
                f"attempts={self.attempts}/{self.max_retries}"
            )
        self.status = JobStatus.PENDING
        self.error_message = ""
        self.updated_at = datetime.now(UTC)
