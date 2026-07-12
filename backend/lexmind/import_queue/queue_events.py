"""Domain events for the Import Queue."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class RequestEnqueued(DomainEvent):
    """Raised when an import request is placed into the queue."""

    request_id: str = ""
    workspace_id: str = ""
    location: str = ""
    priority: int = 0


@dataclass(frozen=True, slots=True)
class RequestDequeued(DomainEvent):
    """Raised when a request is dequeued for processing."""

    request_id: str = ""
    workspace_id: str = ""
    location: str = ""
    priority: int = 0


@dataclass(frozen=True, slots=True)
class RequestCompleted(DomainEvent):
    """Raised when an import request completes successfully."""

    request_id: str = ""
    workspace_id: str = ""
    location: str = ""
    document_id: str = ""
    file_hash: str = ""


@dataclass(frozen=True, slots=True)
class RequestFailed(DomainEvent):
    """Raised when an import request fails."""

    request_id: str = ""
    workspace_id: str = ""
    location: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class RequestCancelled(DomainEvent):
    """Raised when an import request is cancelled."""

    request_id: str = ""
    workspace_id: str = ""


@dataclass(frozen=True, slots=True)
class DuplicateRejected(DomainEvent):
    """Raised when a duplicate request is rejected by deduplication."""

    request_id: str = ""
    workspace_id: str = ""
    location: str = ""
    reason: str = ""
