"""Worker framework domain events.

Worker-level observability events, distinct from the job-level events
emitted by the scheduler/executor. They describe the worker runtime and the
tasks it picks up.
"""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkerStarted(DomainEvent):
    """Raised when a worker runtime starts."""

    worker_id: str = ""
    pool_size: int = 1


@dataclass(frozen=True, slots=True)
class WorkerStopped(DomainEvent):
    """Raised when a worker runtime stops."""

    worker_id: str = ""


@dataclass(frozen=True, slots=True)
class TaskAssigned(DomainEvent):
    """Raised when a worker picks up a job for execution."""

    job_id: str = ""
    job_type: str = ""
    workspace_id: str = ""


@dataclass(frozen=True, slots=True)
class TaskCompleted(DomainEvent):
    """Raised when a worker finishes a job successfully."""

    job_id: str = ""
    job_type: str = ""
    result: str = ""


@dataclass(frozen=True, slots=True)
class TaskFailed(DomainEvent):
    """Raised when a worker's job fails."""

    job_id: str = ""
    job_type: str = ""
    error_message: str = ""
