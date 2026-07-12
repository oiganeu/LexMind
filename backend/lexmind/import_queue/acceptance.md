# Import Queue - Acceptance Criteria

> Task 27 - Design the framework for an Import Queue.

## Deliverables

- [x] Interfaces (Protocols): `ImportQueue`, `ImportQueueRepository`,
      `DeduplicationStrategy`
- [x] Entities: `ImportRequest`, `RequestStatus` (FSM), `RequestPriority`
- [x] Implementation: `ImportQueueService`, `ChecksumDedup`, `ImportQueuePlugin`
- [x] Domain events: 6 events in `queue_events.py`
- [x] README.md
- [x] Tests: `tests/unit/test_import_queue.py`
- [x] Acceptance criteria: this file

## Functional criteria

1. `submit()` creates a `PENDING` request and emits `RequestEnqueued`.
2. `submit()` with empty `workspace_id` or `location` raises `ValueError`.
3. `submit()` with a duplicate (per `DeduplicationStrategy`) raises
   `DuplicateRequestError` and emits `DuplicateRejected`.
4. `dequeue()` returns the highest-priority pending request, transitions it to
   `DEQUEUED`, and emits `RequestDequeued`.
5. `dequeue()` returns `None` when the queue is empty.
6. `cancel()` transitions a non-terminal request to `CANCELLED` and emits
   `RequestCancelled`; returns `False` for unknown or terminal requests.
7. `mark_completed()` / `mark_failed()` move a request to a terminal state and
   emit the corresponding event.
8. `pending_ids()` returns the ids of all pending requests.
9. `size()` returns the count of pending requests.

## State-machine criteria

10. `RequestStatus` transitions follow the documented FSM.
11. Invalid transitions raise `InvalidRequestStateError`.
12. `ImportRequest.is_terminal` is `True` for COMPLETED/FAILED/CANCELLED.
13. `ImportRequest.can_retry` is `True` only when FAILED and `retries <
    max_retries`.
14. `ImportRequest.retry()` resets to PENDING and increments `retries`.

## Architectural criteria

15. `ImportQueueRepository`, `DeduplicationStrategy`, and `ImportQueue` are
    `Protocol` definitions. The domain layer imports no infrastructure.
16. `ImportQueueService` receives all collaborators via constructor injection
    (no singletons, no global state).
17. EventBus integration is optional: all event emission is a no-op when the
    bus is `None`.
18. `ImportQueuePlugin` extends `BasePlugin` and advertises
    `PluginCapability.IMPORT_QUEUE`.
19. `ImportQueuePlugin.stop()` cancels all pending requests.

## Quality criteria

20. All public classes have docstrings.
21. No `print()` calls; `structlog` is used for logging.
22. No `os.path`; `pathlib` / `PurePosixPath` used where needed.
23. Source files are ASCII-only.
24. `ruff` passes with no errors or warnings.
25. Test coverage of `lexmind/import_queue/` is >= 95%.
26. Full unit suite (`uv run pytest tests/unit`) passes.
