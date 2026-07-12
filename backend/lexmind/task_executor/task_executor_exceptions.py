"""Domain exceptions for the task executor package."""

from __future__ import annotations


class TaskExecutorError(Exception):
    """Base error for task executor failures."""


class InvalidTaskStateError(TaskExecutorError):
    """Raised when an invalid task state transition is requested."""


class TaskHandlerNotFoundError(TaskExecutorError):
    """Raised when no handler is registered for a task type."""
