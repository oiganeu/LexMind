"""Queue repository protocol.

Defines the persistence contract for :class:`ImportRequest` entities without
coupling the domain to any concrete storage backend.
"""

from __future__ import annotations

from typing import Protocol

from lexmind.import_queue.import_request import ImportRequest


class ImportQueueRepository(Protocol):
    """Persistence contract for ImportRequest entities."""

    def create(self, request: ImportRequest) -> ImportRequest:
        """Persist a new import request."""
        ...

    def get_by_id(self, request_id: str) -> ImportRequest | None:
        """Retrieve a request by its ID."""
        ...

    def update(self, request: ImportRequest) -> ImportRequest:
        """Update an existing request."""
        ...

    def delete(self, request_id: str) -> None:
        """Delete a request."""
        ...

    def list_pending(
        self, workspace_id: str | None = None, priority: int | None = None
    ) -> list[ImportRequest]:
        """List pending requests, optionally filtered by workspace or priority."""
        ...

    def count_pending(self) -> int:
        """Return the number of pending requests."""
        ...

    def get_queued(self, workspace_id: str) -> list[ImportRequest]:
        """Return queued/dequeued requests for a workspace (ready for processing)."""
        ...
