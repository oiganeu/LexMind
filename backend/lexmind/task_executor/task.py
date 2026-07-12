"""Task entity and lifecycle state machine.

A :class:`Task` is the atomic unit of work executed by the Task Executor. It
carries its own retry and timeout configuration and tracks execution status
independently of the job/scheduler domain.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, unique

from lexmind.task_executor.task_executor_exceptions import InvalidTaskStateError


@unique
class TaskStatus(StrEnum):
    """Lifecycle states of a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset({TaskStatus.PENDING, TaskStatus.CANCELLED}),
    TaskStatus.CANCELLED: frozenset(),
}


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    """Return True if the task may move from *current* to *target*."""
    return target in _TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Outcome of a task execution."""

    task_id: str
    status: TaskStatus
    result: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class Task:
    """Immutable record of a unit of work."""

    task_type: str
    name: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    payload: dict[str, str] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_retries: int = 0
    timeout_seconds: float = 0.0
    result: str = ""
    error_message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.task_type:
            raise ValueError("Task must have a task_type")

    def transition_to(self, target: TaskStatus) -> None:
        """Validate and apply a state transition."""
        if not can_transition(self.status, target):
            raise InvalidTaskStateError(
                f"Cannot transition task {self.task_id} from "
                f"{self.status} to {target}"
            )
        now = datetime.now(UTC)
        if target == TaskStatus.RUNNING and self.started_at is None:
            object.__setattr__(self, "started_at", now)
        if target in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            object.__setattr__(self, "completed_at", now)
        object.__setattr__(self, "status", target)

    @property
    def is_terminal(self) -> bool:
        """Return True if the task is in a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def can_retry(self) -> bool:
        """Return True if the task can be retried."""
        return self.status in (
            TaskStatus.PENDING,
            TaskStatus.FAILED,
        ) and self.attempts < self.max_retries

    def retry(self) -> None:
        """Reset to PENDING for another attempt."""
        if not self.can_retry:
            raise ValueError("Task cannot be retried")
        object.__setattr__(self, "status", TaskStatus.PENDING)
        object.__setattr__(self, "error_message", "")
