"""Import Queue framework.

Coordinates import requests across the LexMind platform: priority ordering,
queue-level deduplication, lifecycle tracking, and downstream job submission.

Public API:

- :class:`ImportRequest` / :class:`RequestStatus` / :class:`RequestPriority`
- :class:`ImportQueue` (Protocol) / :class:`ImportQueueService`
- :class:`ImportQueueRepository` (Protocol)
- :class:`DeduplicationStrategy` / :class:`ChecksumDedup`
- :class:`ImportQueuePlugin`
- Queue domain events (see :mod:`lexmind.import_queue.queue_events`)
"""

from lexmind.import_queue.import_queue import (
    ImportQueue,
    ImportQueueService,
)
from lexmind.import_queue.import_request import (
    ImportRequest,
    RequestPriority,
    RequestStatus,
)
from lexmind.import_queue.queue_plugin import ImportQueuePlugin
from lexmind.import_queue.queue_repository import ImportQueueRepository

__all__ = [
    "ImportRequest",
    "RequestPriority",
    "RequestStatus",
    "ImportQueue",
    "ImportQueueService",
    "ImportQueuePlugin",
    "ImportQueueRepository",
]
