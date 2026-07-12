"""Import request domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum, unique


@unique
class RequestPriority(IntEnum):
    """Priority levels for import requests."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

    @property
    def weight(self) -> int:
        """Return priority weight for queue ordering."""
        return int(self)


@unique
class RequestStatus(StrEnum):
    """Lifecycle states of an import request."""

    PENDING = "pending"
    DEQUEUED = "dequeued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.PENDING: frozenset(
        {RequestStatus.DEQUEUED, RequestStatus.CANCELLED, RequestStatus.FAILED}
    ),
    RequestStatus.DEQUEUED: frozenset(
        {RequestStatus.PROCESSING, RequestStatus.CANCELLED, RequestStatus.FAILED}
    ),
    RequestStatus.PROCESSING: frozenset(
        {RequestStatus.COMPLETED, RequestStatus.CANCELLED, RequestStatus.FAILED}
    ),
    RequestStatus.COMPLETED: frozenset(),
    RequestStatus.FAILED: frozenset(
        {RequestStatus.PENDING, RequestStatus.CANCELLED}
    ),
    RequestStatus.CANCELLED: frozenset(),
}


def can_transition(current: RequestStatus, target: RequestStatus) -> bool:
    """Return True if the request may move from *current* to *target*."""
    return target in _TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class ImportRequest:
    """Immutable record of an import request."""

    workspace_id: str
    location: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: RequestPriority = RequestPriority.NORMAL
    status: RequestStatus = RequestStatus.PENDING
    payload: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("Import request must belong to a workspace")
        if self.retries >= self.max_retries:
            raise ValueError("Request retries exceed max retries")

    def transition_to(self, target: RequestStatus) -> None:
        """Validate and apply a state transition."""
        if not can_transition(self.status, target):
            from lexmind.import_queue.import_queue_exceptions import InvalidRequestStateError
            raise InvalidRequestStateError(
                f"Cannot transition request {self.request_id} from {self.status} to {target}"
            )
        now = datetime.now(UTC)
        if target == RequestStatus.PROCESSING and self.started_at is None:
            object.__setattr__(self, "started_at", now)
        if target in (RequestStatus.COMPLETED, RequestStatus.CANCELLED, RequestStatus.FAILED):
            object.__setattr__(self, "completed_at", now)
        object.__setattr__(self, "status", target)

    @property
    def is_terminal(self) -> bool:
        """Return True if the request is in a terminal state."""
        return self.status in (
            RequestStatus.COMPLETED,
            RequestStatus.CANCELLED,
            RequestStatus.FAILED,
        )

    @property
    def can_retry(self) -> bool:
        """Return True if the request can be retried."""
        return (
            self.status == RequestStatus.FAILED
            and self.retries < self.max_retries
        )

    def retry(self) -> None:
        """Reset to PENDING for retry."""
        if not self.can_retry:
            raise ValueError("Request cannot be retried")
        object.__setattr__(self, "status", RequestStatus.PENDING)
        object.__setattr__(self, "retries", self.retries + 1)

    def to_job_payload(self) -> dict[str, str]:
        """Convert request to a payload suitable for Job submission."""
        payload = self.payload.copy()
        payload.update(
            {
                "workspace_id": self.workspace_id,
                "location": self.location,
                "request_id": self.request_id,
            }
        )
        return payload
