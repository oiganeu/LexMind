"""Task executor service.

The :class:`TaskExecutorService` runs a :class:`Task` by dispatching it to a
registered :class:`TaskHandler`. Unlike the job executor, which only
dispatches work by type, the task executor owns a resilient execution loop:
it tracks attempts, retries on failure up to ``max_retries``, and records
terminal outcomes. The retry delay is injected so callers control timing
without coupling to wall-clock sleep.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lexmind.events.event_bus import EventBus
from lexmind.task_executor.task import Task, TaskStatus
from lexmind.task_executor.task_events import (
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskRetriedEvent,
    TaskStartedEvent,
    TaskSubmittedEvent,
)
from lexmind.task_executor.task_executor_exceptions import InvalidTaskStateError
from lexmind.task_executor.task_registry import TaskHandler, TaskRegistry


class TaskExecutor(Protocol):
    """Executes tasks and reports their terminal outcome."""

    def execute(self, task: Task) -> Task:
        """Execute *task* with retries and return the updated task."""
        ...

    def cancel(self, task: Task) -> Task:
        """Cancel *task* if it has not reached a terminal state."""
        ...


def _noop_delay(_seconds: float) -> None:  # pragma: no cover - default no-op
    return None


class TaskExecutorService:
    """Default task executor implementation."""

    def __init__(
        self,
        registry: TaskRegistry,
        event_bus: EventBus | None = None,
        delay: Callable[[float], None] = _noop_delay,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._delay = delay

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def execute(self, task: Task) -> Task:
        """Execute *task* with built-in retry support."""
        if task.status is not TaskStatus.PENDING:
            raise InvalidTaskStateError(
                f"Task {task.task_id} must be PENDING to execute, got {task.status}"
            )
        self._emit(
            TaskSubmittedEvent(
                task_id=task.task_id,
                task_type=task.task_type,
                aggregate_id=task.task_id,
            )
        )

        handler: TaskHandler = self._registry.get(task.task_type)
        task.transition_to(TaskStatus.RUNNING)
        attempt = 0
        while True:
            attempt += 1
            object.__setattr__(task, "attempts", attempt)
            self._emit(
                TaskStartedEvent(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    attempt=attempt,
                    aggregate_id=task.task_id,
                )
            )
            try:
                result = handler.execute(task)
            except Exception as exc:  # noqa: BLE001 - executor captures all failures
                object.__setattr__(task, "error_message", str(exc))
                if attempt <= task.max_retries:
                    self._emit(
                        TaskRetriedEvent(
                            task_id=task.task_id,
                            task_type=task.task_type,
                            attempt=attempt + 1,
                            aggregate_id=task.task_id,
                        )
                    )
                    self._delay(
                        task.timeout_seconds if task.timeout_seconds else 0.0
                    )
                    continue
                task.transition_to(TaskStatus.FAILED)
                self._emit(
                    TaskFailedEvent(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        error_message=task.error_message,
                        attempts=attempt,
                        aggregate_id=task.task_id,
                    )
                )
                return task

            object.__setattr__(task, "result", result)
            task.transition_to(TaskStatus.COMPLETED)
            self._emit(
                TaskCompletedEvent(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    result=result,
                    attempts=attempt,
                    aggregate_id=task.task_id,
                )
            )
            return task

    def cancel(self, task: Task) -> Task:
        """Cancel *task* if it is still pending or running."""
        if task.is_terminal:
            raise InvalidTaskStateError(
                f"Cannot cancel task {task.task_id} in state {task.status}"
            )
        previous = task.status
        task.transition_to(TaskStatus.CANCELLED)
        self._emit(
            TaskCancelledEvent(
                task_id=task.task_id,
                task_type=task.task_type,
                previous_status=previous,
                aggregate_id=task.task_id,
            )
        )
        return task

    def execute_batch(self, tasks: list[Task]) -> list[Task]:
        """Execute every task and return the updated tasks."""
        return [self.execute(task) for task in tasks]
