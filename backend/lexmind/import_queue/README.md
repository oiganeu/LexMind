# Import Queue

> Task 27 - Design the framework for an Import Queue.

The Import Queue coordinates import requests across LexMind. It accepts
high-level import requests from multiple sources (API, File Watcher, drag &
drop), applies priority ordering and queue-level deduplication, tracks the
lifecycle of each request, and hands work off to the downstream ingestion
framework.

This package is framework-only: it defines **interfaces**, **entities**, and
**events**. It performs **no** file IO, OCR, parsing, or persistence of its
own - those are delegated to injected collaborators.

## Responsibilities

- Accept import requests with a priority
- Reject duplicates before they enter the queue
- Order pending requests by priority
- Track request lifecycle (state machine)
- Emit lifecycle domain events
- Hand requests to the downstream ingestion layer

## Components

| Component | Type | Role |
|-----------|------|------|
| `ImportRequest` | entity | Immutable record of an import request |
| `RequestStatus` | FSM | Lifecycle states of a request |
| `RequestPriority` | value object | Priority levels (LOW/NORMAL/HIGH/CRITICAL) |
| `ImportQueue` | Protocol | Public orchestration contract |
| `ImportQueueService` | implementation | Submit / dequeue / cancel / track |
| `ImportQueueRepository` | Protocol | Persistence contract for requests |
| `DeduplicationStrategy` | Protocol | Decides whether a request is a duplicate |
| `ChecksumDedup` | implementation | SHA-256 based dedup via StorageManager |
| `ImportQueuePlugin` | plugin | Registers the service with the plugin framework |

## Dependency flow

```
ImportQueueService --> ImportQueueRepository (Protocol)
                    --> DeduplicationStrategy (Protocol)
                    --> EventBus (optional, injected)

ImportQueuePlugin --> ImportQueueService
                    --> PluginCapability.IMPORT_QUEUE
```

`ImportQueueService` depends only on the `ImportQueueRepository` and
`DeduplicationStrategy` Protocols and an optional EventBus. Concrete
implementations (SQLite repository, storage-backed dedup) are injected, so the
orchestration logic is fully backend-independent.

## Behaviour

1. A request is submitted via `submit(workspace_id, location, priority)`.
2. If a `DeduplicationStrategy` is configured and reports a duplicate, the
   request is rejected and a `DuplicateRejected` event is emitted.
3. Otherwise the request is persisted as `PENDING` and a `RequestEnqueued`
   event is emitted.
4. `dequeue()` returns the highest-priority pending request, transitions it to
   `DEQUEUED`, and emits `RequestDequeued`.
5. After downstream processing, `mark_completed()` / `mark_failed()` move the
   request to a terminal state and emit the corresponding event.
6. `cancel()` transitions a non-terminal request to `CANCELLED`.

## Request states

```
PENDING --> DEQUEUED --> PROCESSING --> COMPLETED
PENDING --> CANCELLED
DEQUEUED --> FAILED
PROCESSING --> FAILED
FAILED --> PENDING (retry)
```

Transitions are validated by `can_transition`; invalid transitions raise
`InvalidRequestStateError`.

## Events

`queue.request_enqueued`, `queue.request_dequeued`,
`queue.request_completed`, `queue.request_failed`,
`queue.request_cancelled`, `queue.duplicate_rejected`.

## Example

```python
from lexmind.import_queue import (
    ImportQueueService,
    ImportQueueRepository,
    ChecksumDedup,
)

service = ImportQueueService(
    repository=repo,           # implements ImportQueueRepository
    deduplication=ChecksumDedup(storage_manager),
    event_bus=event_bus,
)

req = service.submit("ws-1", "storage://ws-1/inbox/a.pdf", priority=2)
next_req = service.dequeue()
service.mark_completed(next_req.request_id, document_id="doc-123")
```

See `lexmind/import_queue/acceptance.md` for the acceptance criteria and
`tests/unit/test_import_queue.py` for the behavioural contract.
