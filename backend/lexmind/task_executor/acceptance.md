# Task Executor - Acceptance Criteria (Task 30)

## AC-1: Task lifecycle state machine
- [x] `Task` defaults to `PENDING` with a generated `task_id`.
- [x] A `Task` without a `task_type` cannot be created (raises `ValueError`).
- [x] Valid transitions move the task through `PENDING -> RUNNING ->
      COMPLETED/FAILED/CANCELLED`, and `FAILED -> PENDING` on retry.
- [x] Invalid transitions raise `InvalidTaskStateError`.
- [x] `started_at` is set on the first transition to `RUNNING`; `completed_at`
      is set on any terminal transition.

## AC-2: Registry and handlers
- [x] `TaskRegistry.register` maps a `task_type` to a `TaskHandler`.
- [x] `TaskRegistry.get` returns the handler or raises `TaskHandlerNotFoundError`.
- [x] Registering an empty `task_type` or a `None` handler raises `ValueError`.
- [x] `has` / `registered_types` reflect current registrations.

## AC-3: Resilient execution
- [x] A successful handler produces a `COMPLETED` task with its result and
      `attempts == 1`, emitting `TaskSubmittedEvent`, `TaskStartedEvent`,
      `TaskCompletedEvent`.
- [x] A handler that always fails and `max_retries == 0` yields a `FAILED`
      task with `error_message` and a `TaskFailedEvent`.
- [x] A transient failure is retried up to `max_retries`; each retry emits a
      `TaskRetriedEvent` and invokes the injected `delay`.
- [x] After exhausting retries the task is `FAILED` with `TaskFailedEvent`.
- [x] Executing a non-`PENDING` task raises `InvalidTaskStateError`.

## AC-4: Cancellation
- [x] `cancel` moves a pending/running task to `CANCELLED` and emits
      `TaskCancelledEvent` with the previous status.
- [x] `cancel` on a terminal task raises `InvalidTaskStateError`.

## AC-5: Plugin integration
- [x] `TaskExecutorPlugin` declares `PluginCapability.TASK_EXECUTOR`.
- [x] `register_handler` contributes handlers into the plugin's registry.
- [x] `start` / `stop` transition the plugin state.

## AC-6: Quality gates
- [x] Framework-only: no infrastructure imports in `lexmind/task_executor/`.
- [x] All public classes/Protocols have docstrings.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Unit tests cover the package at 100%.
