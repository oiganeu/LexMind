"""Domain events emitted by the task executor.

These events describe the lifecycle of task execution and are published
through the EventBus so other parts of the system can react to task
progress without coupling to the executor implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent
from lexmind.task_executor.task import TaskStatus


@dataclass(frozen=True, slots=True)
class TaskSubmittedEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a task is submitted for execution."""

    task_id: str = ""
    task_type: str = ""


@dataclass(frozen=True, slots=True)
class TaskStartedEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a task begins a (re)try."""

    task_id: str = ""
    task_type: str = ""
    attempt: int = 0


@dataclass(frozen=True, slots=True)
class TaskCompletedEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a task finishes successfully."""

    task_id: str = ""
    task_type: str = ""
    result: str = ""
    attempts: int = 0


@dataclass(frozen=True, slots=True)
class TaskFailedEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a task exhausts its retries and fails."""

    task_id: str = ""
    task_type: str = ""
    error_message: str = ""
    attempts: int = 0


@dataclass(frozen=True, slots=True)
class TaskRetriedEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a failed attempt is followed by another attempt."""

    task_id: str = ""
    task_type: str = ""
    attempt: int = 0


@dataclass(frozen=True, slots=True)
class TaskCancelledEvent(DomainEvent):  # pragma: no cover - trivial dataclass
    """Emitted when a task is cancelled before completion."""

    task_id: str = ""
    task_type: str = ""
    previous_status: TaskStatus = TaskStatus.PENDING
