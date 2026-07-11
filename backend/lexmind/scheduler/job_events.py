"""Job lifecycle domain events."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class JobCreated(DomainEvent):
    """Raised when a new job is created and enqueued."""

    workspace_id: str = ""
    job_type: str = ""


@dataclass(frozen=True, slots=True)
class JobStarted(DomainEvent):
    """Raised when a job begins execution."""

    workspace_id: str = ""
    job_type: str = ""


@dataclass(frozen=True, slots=True)
class JobCompleted(DomainEvent):
    """Raised when a job finishes successfully."""

    workspace_id: str = ""
    job_type: str = ""
    result: str = ""


@dataclass(frozen=True, slots=True)
class JobFailed(DomainEvent):
    """Raised when a job fails."""

    workspace_id: str = ""
    job_type: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class JobCancelled(DomainEvent):
    """Raised when a job is cancelled."""

    workspace_id: str = ""
    job_type: str = ""
