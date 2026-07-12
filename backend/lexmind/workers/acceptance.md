# Worker Framework - Acceptance Criteria

> Task 29 - Design the framework for a Worker Framework.

## Deliverables

- [x] Interfaces (Protocols): `Worker`, `TaskHandler`
- [x] Services: `WorkerService`, `WorkerPool`, `WorkerRegistry`
- [x] Plugin: `WorkerPlugin` (PluginCapability.WORKER)
- [x] Domain events: 5 events in `worker_events.py`
- [x] README.md
- [x] Tests: `tests/unit/test_workers.py`
- [x] Acceptance criteria: this file

## Functional criteria

1. `WorkerService.register()` stores a handler in the registry and the
   executor for the given job type.
2. `WorkerService.run_once()` returns `None` when the queue is empty.
3. `WorkerService.run_once()` executes a pending job via the scheduler and
   emits `TaskAssigned`, then `TaskCompleted` (success) or `TaskFailed`
   (failure) based on job status.
4. `WorkerService.run_all()` drains the queue and returns all executed jobs.
5. `WorkerService.start()` / `stop()` toggle `is_running` and emit
   `WorkerStarted` / `WorkerStopped`.
6. `WorkerPool` is created with `pool_size >= 1` (smaller raises
   `ValueError`).
7. `WorkerPool.register()` registers a handler across all workers.
8. `WorkerPool.run_once()` dispatches jobs in round-robin order.
9. `WorkerPool.start_all()` / `stop_all()` start/stop every worker.
10. `WorkerPool.size` equals `pool_size`; `is_running` is True when any
    worker is running.

## Plugin criteria

11. `WorkerPlugin` extends `BasePlugin` and advertises
    `PluginCapability.WORKER`.
12. `WorkerPlugin.start()` starts the underlying worker (or pool);
    `stop()` stops it.

## Architectural criteria

13. `Worker` and `TaskHandler` are `Protocol` definitions.
14. `WorkerService` receives all collaborators via constructor injection
    (no singletons, no global state).
15. EventBus integration is optional: event emission is a no-op when the bus
    is `None`.
16. The worker never imports storage/execution infrastructure directly; it
    depends only on the injected `JobScheduler`, `JobExecutor`,
    `WorkerRegistry`, and optional `EventBus`.

## Quality criteria

17. All public classes have docstrings.
18. No `print()` calls; `structlog` is used for logging.
19. No `os.path`; `pathlib` used where needed.
20. Source files are ASCII-only.
21. `ruff` passes with no errors or warnings.
22. Test coverage of `lexmind/workers/` is >= 95%.
23. Full unit suite (`uv run pytest tests/unit`) passes.
