"""Default Import Queue implementation.

Forms a coordination layer between ImportRequest entities (pending),
DeduplicationStrategy (rejection), and downstream submission (Job creation).
"""

from __future__ import annotations

import structlog

from lexmind.import_queue import import_queue_exceptions as exc
from lexmind.import_queue.import_request import (
    ImportRequest,
    RequestStatus,
)
from lexmind.import_queue.queue_events import (
    DuplicateRejected,
    RequestCancelled,
    RequestCompleted,
    RequestDequeued,
    RequestEnqueued,
    RequestFailed,
)
from lexmind.import_queue.queue_repository import ImportQueueRepository

logger = structlog.get_logger(__name__)


class ImportQueue:
    """Public contract of the import queue framework."""

    def submit(
        self,
        workspace_id: str,
        location: str,
        priority: int = 1,
        payload: dict[str, str] | None = None,
    ) -> ImportRequest:
        """Create and enqueue a new import request."""
        ...

    def dequeue(self) -> ImportRequest | None:
        """Return the highest-priority pending request, marking it dequeued."""
        ...

    def get_job(self, request_id: str) -> ImportRequest | None:
        """Return a request by id, or None if not found."""
        ...

    def cancel(self, request_id: str) -> bool:
        """Cancel a pending or dequeued request."""
        ...

    def pending_ids(self) -> list[str]:
        """Return the ids of all pending requests."""
        ...

    def size(self) -> int:
        """Return the number of pending requests."""
        ...


class ImportQueueService:
    """Default ImportQueue implementation.

    Coordinates request lifecycle: submits with dedup, dequeues by priority,
    tracks state transitions, and emits domain events through an optional
    EventBus.

    Args:
        repository: Persistence backend for requests (Protocol).
        deduplication: Optional duplicate-detection strategy.
        event_bus: Optional bus for lifecycle events (noop when None).
    """

    def __init__(
        self,
        repository: ImportQueueRepository,
        deduplication: object | None = None,
        event_bus: object | None = None,
    ) -> None:
        self._repo = repository
        self._dedup = deduplication
        self._bus = event_bus

    def submit(
        self,
        workspace_id: str,
        location: str,
        priority: int = 1,
        payload: dict[str, str] | None = None,
    ) -> ImportRequest:
        """Create and enqueue a new import request.

        Raises:
            DuplicateRequestError: If a deduplication strategy marks the
                request as a duplicate.
            ValueError: If workspace_id or location is empty.
        """
        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not location:
            raise ValueError("location is required")

        request = ImportRequest(
            workspace_id=workspace_id,
            location=location,
            priority=priority,
            payload=payload or {},
        )

        if self._dedup is not None and self._dedup.is_duplicate(request):
            logger.info("request_duplicate_rejected", location=location)
            self._emit(
                DuplicateRejected(
                    workspace_id=workspace_id,
                    location=location,
                    reason="duplicate-detected",
                )
            )
            raise exc.DuplicateRequestError(
                f"Duplicate import request for {location}"
            )

        request = self._repo.create(request)
        self._emit(
            RequestEnqueued(
                request_id=request.request_id,
                workspace_id=workspace_id,
                location=location,
                priority=request.priority,
            )
        )
        logger.info("request_submitted", request_id=request.request_id)
        return request

    def dequeue(self) -> ImportRequest | None:
        """Return the highest-priority pending request, marking it dequeued."""
        pending = self._repo.list_pending()
        if not pending:
            return None
        pending.sort(key=lambda r: r.priority, reverse=True)
        request = pending[0]
        request.transition_to(RequestStatus.DEQUEUED)
        request = self._repo.update(request)
        self._emit(
            RequestDequeued(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                location=request.location,
                priority=request.priority,
            )
        )
        logger.info("request_dequeued", request_id=request.request_id)
        return request

    def get_job(self, request_id: str) -> ImportRequest | None:
        """Return a request by id, or None if not found."""
        return self._repo.get_by_id(request_id)

    def cancel(self, request_id: str) -> bool:
        """Cancel a pending or dequeued request.

        Returns True if the request was cancelled, False if it was not found
        or was already in a terminal state.
        """
        request = self._repo.get_by_id(request_id)
        if request is None:
            return False
        if request.is_terminal:
            return False
        request.transition_to(RequestStatus.CANCELLED)
        self._repo.update(request)
        self._emit(
            RequestCancelled(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
            )
        )
        logger.info("request_cancelled", request_id=request.request_id)
        return True

    def mark_completed(
        self, request_id: str, document_id: str = "", file_hash: str = ""
    ) -> None:
        """Mark a request as completed (called after downstream import)."""
        request = self._repo.get_by_id(request_id)
        if request is None:
            return
        if request.status == RequestStatus.DEQUEUED:
            request.transition_to(RequestStatus.PROCESSING)
        request.transition_to(RequestStatus.COMPLETED)
        self._repo.update(request)
        self._emit(
            RequestCompleted(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                location=request.location,
                document_id=document_id,
                file_hash=file_hash,
            )
        )
        logger.info("request_completed", request_id=request.request_id)

    def mark_failed(self, request_id: str, error_message: str = "") -> None:
        """Mark a request as failed (called after downstream import)."""
        request = self._repo.get_by_id(request_id)
        if request is None:
            return
        if request.status == RequestStatus.DEQUEUED:
            request.transition_to(RequestStatus.PROCESSING)
        request.transition_to(RequestStatus.FAILED)
        self._repo.update(request)
        self._emit(
            RequestFailed(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                location=request.location,
                error_message=error_message,
            )
        )
        logger.info("request_failed", request_id=request.request_id)

    def pending_ids(self) -> list[str]:
        """Return the ids of all pending requests."""
        return [r.request_id for r in self._repo.list_pending()]

    def size(self) -> int:
        """Return the number of pending requests."""
        return self._repo.count_pending()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._bus is not None:
            self._bus.publish(event)  # type: ignore[attr-defined]
