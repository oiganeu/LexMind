"""Task handler protocol and registry.

A :class:`TaskHandler` performs the actual work for a task type. The
:class:`TaskRegistry` maps task types to their handlers and is the single
extension point the Task Executor uses to dispatch work.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lexmind.task_executor.task import Task
from lexmind.task_executor.task_executor_exceptions import TaskHandlerNotFoundError


@runtime_checkable
class TaskHandler(Protocol):
    """Executes a task and returns a textual result."""

    def execute(self, task: Task) -> str:
        """Run *task* and return its result as a string."""
        ...


class TaskRegistry:
    """Registry mapping task types to :class:`TaskHandler` implementations."""

    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, task_type: str, handler: TaskHandler) -> None:
        """Register *handler* for *task_type*."""
        if not task_type:
            raise ValueError("task_type must not be empty")
        if handler is None:
            raise ValueError("handler must not be None")
        self._handlers[task_type] = handler

    def get(self, task_type: str) -> TaskHandler:
        """Return the handler for *task_type* or raise."""
        handler = self._handlers.get(task_type)
        if handler is None:
            raise TaskHandlerNotFoundError(
                f"No handler registered for task type '{task_type}'"
            )
        return handler

    def has(self, task_type: str) -> bool:
        """Return True if a handler is registered for *task_type*."""
        return task_type in self._handlers

    def registered_types(self) -> list[str]:
        """Return the registered task types."""
        return sorted(self._handlers)
