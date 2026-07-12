# Worker Framework

> Task 29 - Design the framework for a Worker Framework.

The Worker Framework is the runtime that executes scheduled jobs. It pulls
pending jobs from a `JobScheduler`, ensures the correct `TaskHandler` is
registered with the scheduler's executor, runs the work, and emits
worker-level lifecycle events. A `WorkerPool` coordinates multiple workers
for concurrency.

This package is framework-only: it defines **interfaces**, **entities**, and
**behaviour**. It performs **no** I/O of its own; persistence and execution
are delegated to the injected `JobScheduler` and `JobExecutor`.

## Responsibilities

- Register task handlers per job type
- Drive job execution from the scheduler
- Emit worker-level lifecycle events
- Support a pool of concurrent workers
- Integrate with the plugin framework

## Components

| Component | Type | Role |
|-----------|------|------|
| `Worker` | Protocol | Public worker runtime contract |
| `WorkerService` | implementation | Runs jobs from a scheduler, emits events |
| `WorkerPool` | implementation | Coordinates multiple workers |
| `TaskHandler` | Protocol | Performs the work for a job type |
| `WorkerRegistry` | implementation | Maps job types to handlers |
| `WorkerPlugin` | plugin | Registers the worker with the plugin framework |

## Dependency flow

```
WorkerService --> JobScheduler (source + executor)
               --> JobExecutor (handler receiver)
               --> WorkerRegistry (handler lookup)
               --> EventBus (optional, injected)
WorkerPool --> N x WorkerService
WorkerPlugin --> Worker (WorkerService | WorkerPool)
```

`WorkerService` depends only on injected collaborators (`JobScheduler`,
`JobExecutor`, `WorkerRegistry`, optional `EventBus`). It never imports
storage or execution infrastructure directly, keeping the runtime backend
agnostic.

## Behaviour

1. A `TaskHandler` is registered for a job type via `register()`.
2. `run_once()` asks the scheduler for the next pending job
   (`process_next`), which executes it through the executor using the
   registered handler.
3. The worker emits `TaskAssigned` when it picks up the job, then
   `TaskCompleted` or `TaskFailed` based on the resulting job status.
4. `run_all()` drains the queue; `start()`/`stop()` flip the runtime flag
   and emit `WorkerStarted` / `WorkerStopped`.
5. A `WorkerPool` runs `pool_size` workers and dispatches jobs in
   round-robin order.

## Events

`worker.started`, `worker.stopped`, `worker.task_assigned`,
`worker.task_completed`, `worker.task_failed`.

## Example

```python
from lexmind.workers import WorkerService, WorkerRegistry, WorkerPlugin
from lexmind.scheduler import JobScheduler, JobExecutor, SqliteJobRepositoryImpl

repo = SqliteJobRepositoryImpl(session_manager)
queue = JobQueue(repo)
executor = JobExecutor(repo, event_bus=bus)
scheduler = JobScheduler(queue, executor, repo, event_bus=bus)
registry = WorkerRegistry()
worker = WorkerService(scheduler, executor, registry, event_bus=bus)

def handle_ingest(job):
    return f"imported {job.payload}"

worker.register("ingest", handle_ingest)
worker.start()
worker.run_all()
```

See `lexmind/workers/acceptance.md` for the acceptance criteria and
`tests/unit/test_workers.py` for the behavioural contract.
