# Job Scheduler - Acceptance Criteria

> Task 28 - Design the framework for a Job Scheduler.

## Deliverables

- [x] Interfaces (Protocols): `JobRepository`
- [x] Entities: `Job`, `JobStatus` (FSM)
- [x] Services: `JobQueue`, `JobExecutor`, `JobScheduler`, `PipelineDispatcher`
- [x] Persistence: `SqliteJobRepositoryImpl`
- [x] Domain events: 5 events in `job_events.py`
- [x] README.md
- [x] Tests: `tests/unit/test_scheduler.py`
- [x] Acceptance criteria: this file

## Functional criteria

1. `JobScheduler.submit()` creates a `PENDING` job, enqueues it, and emits
   `JobCreated`.
2. `JobScheduler.process_next()` dequeues and executes the highest-priority
   pending job, transitioning it to `RUNNING` then `COMPLETED`/`FAILED`.
3. `JobExecutor.execute()` dispatches to a registered `JobHandler` by
   `job_type`; an unknown type raises `ValueError`.
4. `JobScheduler.retry_job()` resets a `FAILED` job to `PENDING` (while
   `attempts < max_retries`) and re-enqueues it.
5. `JobScheduler.cancel_job()` transitions a non-terminal job to `CANCELLED`.
6. `JobScheduler.recover_pending()` returns queued pending jobs for restart
   recovery.
7. `PipelineDispatcher` bridges pipeline execution requests into scheduler
   jobs.

## State-machine criteria

8. `JobStatus` transitions follow the documented FSM.
9. Invalid transitions raise `ValueError`.
10. `Job.is_terminal` is `True` for COMPLETED/FAILED/CANCELLED.
11. `Job.can_retry` is `True` only when FAILED and `attempts < max_retries`.
12. `Job.retry()` resets to PENDING and increments `attempts`.

## Architectural criteria

13. `JobRepository` is a `Protocol`; only `SqliteJobRepositoryImpl` imports
    SQLAlchemy. Domain never leaks infrastructure.
14. All collaborators are injected via constructor (no singletons, no global
    state).
15. EventBus integration is optional: event emission is a no-op when the bus
    is `None`.
16. `JobRepository` returns domain `Job` entities only.

## Quality criteria

17. All public classes have docstrings.
18. No `print()` calls; `structlog` is used for logging.
19. No `os.path`; `pathlib` used where needed.
20. Source files are ASCII-only.
21. `ruff` passes with no errors or warnings.
22. Test coverage of `lexmind/scheduler/` is 100%.
23. Full unit suite (`uv run pytest tests/unit`) passes.
