# Job Scheduler

> Task 28 - Design the framework for a Job Scheduler.

The Job Scheduler manages pipeline execution as discrete jobs. It provides an
in-memory priority queue, a pluggable execution backend, persistent storage,
lifecycle orchestration, and a bridge that turns pipeline runs into scheduled
jobs.

This package is framework-only: it defines **entities**, **interfaces**, and
**behaviour**. Persistence is delegated to an injected `JobRepository`
(SQLite by default); execution is delegated to registered `JobHandler`
callables.

## Responsibilities

- Create and enqueue pipeline jobs with a priority
- Dequeue and execute the highest-priority pending job
- Persist job state transitions
- Retry failed jobs up to a configurable limit
- Cancel pending or running jobs
- Recover pending jobs after a restart
- Publish lifecycle domain events

## Components

| Component | Type | Role |
|-----------|------|------|
| `Job` | entity | Tracks a single pipeline execution attempt |
| `JobStatus` | FSM | Lifecycle states of a job |
| `JobQueue` | service | In-memory priority queue backed by a repository |
| `JobExecutor` | service | Runs jobs via registered `JobHandler` callables |
| `JobScheduler` | service | Orchestrates submit/execute/retry/cancel/recover |
| `JobRepository` | Protocol | Persistence contract (`Job` entities only) |
| `SqliteJobRepositoryImpl` | implementation | SQLAlchemy/SQLite-backed repository |
| `PipelineDispatcher` | bridge | Translates pipeline runs into scheduler jobs |
| job_events | domain events | `JobCreated`, `JobStarted`, `JobCompleted`, `JobFailed`, `JobCancelled` |

## Dependency flow

```
JobScheduler --> JobQueue --> JobRepository
             --> JobExecutor (JobHandler registry)
             --> EventBus (optional, injected)
PipelineDispatcher --> JobScheduler
```

Every component receives its collaborators via constructor injection. The
domain layer never imports infrastructure: only `SqliteJobRepositoryImpl`
references SQLAlchemy, behind the `JobRepository` Protocol.

## Job states

```
PENDING --> RUNNING --> COMPLETED
PENDING --> RUNNING --> FAILED --> PENDING (retry)
PENDING --> CANCELLED
RUNNING --> CANCELLED
```

Transitions are validated by `can_transition`; invalid transitions raise
`ValueError`. A `FAILED` job may be reset to `PENDING` via `retry()` while
`attempts < max_retries`.

## Events

`job.created`, `job.started`, `job.completed`, `job.failed`, `job.cancelled`.

## Example

```python
from lexmind.scheduler import (
    JobQueue,
    JobExecutor,
    JobScheduler,
    SqliteJobRepositoryImpl,
)

repo = SqliteJobRepositoryImpl(session_manager)
queue = JobQueue(repo)
executor = JobExecutor(repo, event_bus=bus)
scheduler = JobScheduler(queue, executor, repo, event_bus=bus)

scheduler.submit("ws-1", job_type="pipeline", payload={"doc": "doc-1"}, priority=2)
scheduler.process_all()
```

See `lexmind/scheduler/acceptance.md` for the acceptance criteria and
`tests/unit/test_scheduler.py` for the behavioural contract.
