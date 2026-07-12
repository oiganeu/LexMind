"""Task Executor framework.

Resilient execution engine for atomic units of work (tasks) with built-in
retry, timeout metadata and lifecycle events, sitting below the job
scheduler and worker runtimes.
"""

from __future__ import annotations

from lexmind.task_executor.task import (
    Task,
    TaskResult,
    TaskStatus,
    can_transition,
)
from lexmind.task_executor.task_events import (
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskRetriedEvent,
    TaskStartedEvent,
    TaskSubmittedEvent,
)
from lexmind.task_executor.task_executor import (
    TaskExecutor,
    TaskExecutorService,
)
from lexmind.task_executor.task_executor_exceptions import (
    InvalidTaskStateError,
    TaskExecutorError,
    TaskHandlerNotFoundError,
)
from lexmind.task_executor.task_executor_plugin import TaskExecutorPlugin
from lexmind.task_executor.task_registry import TaskHandler, TaskRegistry

__all__ = [
    "Task",
    "TaskResult",
    "TaskStatus",
    "can_transition",
    "TaskSubmittedEvent",
    "TaskStartedEvent",
    "TaskCompletedEvent",
    "TaskFailedEvent",
    "TaskRetriedEvent",
    "TaskCancelledEvent",
    "TaskExecutor",
    "TaskExecutorService",
    "TaskExecutorError",
    "InvalidTaskStateError",
    "TaskHandlerNotFoundError",
    "TaskExecutorPlugin",
    "TaskHandler",
    "TaskRegistry",
]
