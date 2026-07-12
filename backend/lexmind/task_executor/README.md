# Task Executor (Task 30)

The **Task Executor** is the resilient execution engine for atomic units of
work inside LexMind. It sits *below* the job scheduler and the worker
runtimes and is responsible for actually running a single `Task` to its
terminal outcome, handling retries and recording results.

## Position in the architecture

```
JobScheduler  ->  picks jobs due for execution
Worker        ->  runtime that drives jobs
TaskExecutor  ->  runs one Task with retries / timeout (this module)
TaskHandler   ->  pluggable unit of work contributed by other plugins
```

It is intentionally *framework-only*: it has no infrastructure dependencies
(storage, networking, filesystem) and never imports concrete I/O.

## Core abstractions

### `Task` (`task.py`)
Immutable value object describing one unit of work. Carries its own
`max_retries` and `timeout_seconds`, the payload, and the execution status.

`TaskStatus` is a finite state machine:

```
PENDING --start--> RUNNING --ok--> COMPLETED
   |                  |
   | cancel           | fail (attempts > max_retries)
   v                  v
CANCELLED          FAILED --retry--> PENDING
```

`Task.transition_to` validates every transition and records `started_at` /
`completed_at` timestamps. `Task.can_retry` and `Task.retry()` manage the
retry lifecycle.

### `TaskHandler` (`task_registry.py`)
```python
@runtime_checkable
class TaskHandler(Protocol):
    def execute(self, task: Task) -> str: ...
```
A single extension point: any plugin can register a handler for a task type.

### `TaskRegistry` (`task_registry.py`)
Maps `task_type -> TaskHandler`. Raises `TaskHandlerNotFoundError` for
unknown types.

### `TaskExecutor` / `TaskExecutorService` (`task_executor.py`)
`TaskExecutorService.execute(task)`:
1. validates the task is `PENDING`;
2. transitions to `RUNNING` and emits `TaskSubmittedEvent` + `TaskStartedEvent`;
3. calls the registered handler;
4. on success -> `COMPLETED` + `TaskCompletedEvent`;
5. on failure -> retry while `attempt <= max_retries` (emitting
   `TaskRetriedEvent`, invoking the injected `delay`), otherwise
   `FAILED` + `TaskFailedEvent`.

The retry `delay` is an injected callable so callers control timing without
coupling to wall-clock sleep (tests inject a no-op/recording callable).

`cancel(task)` cancels a non-terminal task (`TaskCancelledEvent`).

### Events (`task_events.py`)
`TaskSubmittedEvent`, `TaskStartedEvent`, `TaskCompletedEvent`,
`TaskFailedEvent`, `TaskRetriedEvent`, `TaskCancelledEvent` — all extend
`lexmind.domain.events.base.DomainEvent` and are published through the
`EventBus`.

### `TaskExecutorPlugin` (`task_executor_plugin.py`)
Exposes `PluginCapability.TASK_EXECUTOR`, owns the registry and executor,
and provides `register_handler` so other plugins contribute task handlers.

## Design notes

* **Distinct from `JobExecutor`**: the job executor only dispatches a job to
  a handler by type and relies on the scheduler for retry. The task executor
  owns a resilient execution loop with built-in retries and per-task
  timeout/result metadata — it is the lower-level primitive the higher layers
  build on.
* **No global state, no singletons**: the service is constructed with its
  dependencies (`TaskRegistry`, optional `EventBus`, optional `delay`).
* **ASCII-only, ruff-clean**, 100% unit-test coverage on the package.
