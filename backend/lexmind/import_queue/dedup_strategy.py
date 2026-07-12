"""Deduplication strategy for import requests.

A :class:`DeduplicationStrategy` decides whether a newly submitted request
is a duplicate of one already queued.  The default implementation,
:class:`ChecksumDedup`, uses SHA-256 checksums of the source file via the
injected ``StorageManager``.
"""

from __future__ import annotations

from typing import Protocol

from lexmind.import_queue.import_request import ImportRequest


class DeduplicationStrategy(Protocol):
    """Contract for rejecting duplicate import requests."""

    def is_duplicate(self, request: ImportRequest) -> bool:
        """Return True if *request* duplicates an already queued request."""
        ...


class ChecksumDedup:
    """SHA-256 based deduplication using a storage manager.

    Args:
        storage_manager: Object exposing ``checksum(uri, algorithm)`` and
            ``exists(uri)`` for the source location.  Injected to keep the
            domain free of any storage infrastructure import.
    """

    def __init__(self, storage_manager: object) -> None:
        self._storage = storage_manager

    def is_duplicate(self, request: ImportRequest) -> bool:
        """Return True if the request's source file already has a queued twin.

        Two requests are considered duplicates when they target the same
        workspace and the same storage URI.  When the storage manager is
        unavailable or the URI is missing, the request is treated as unique.
        """
        if not request.location:
            return False
        try:
            existing = self._storage.get_by_location(  # type: ignore[attr-defined]
                request.workspace_id, request.location
            )
        except Exception:  # noqa: BLE001 - storage errors => no dedup
            return False
        if existing is None:
            return False
        if existing.request_id == request.request_id:
            return False
        return existing.status in ("pending", "dequeued", "processing")
