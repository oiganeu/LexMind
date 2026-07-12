"""Worker registry and task handler contract.

A :class:`TaskHandler` performs the actual work for a job type.  The
:class:`WorkerRegistry` maps job types to their handlers so a worker can
dispatch an executed job to the right implementation.
"""

from __future__ import annotations

from typing import Protocol

from lexmind.scheduler.job import Job


class TaskHandler(Protocol):
    """Contract for handling a single job type.

    Implementations receive a :class:`Job` and return a result string.
    Raising inside ``handle`` marks the job as failed by the scheduler.
    """

    def handle(self, job: Job) -> str:
        """Execute the work for *job* and return a result string."""
        ...


class WorkerRegistry:
    """Maps job types to their :class:`TaskHandler` implementations."""

    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, job_type: str, handler: TaskHandler) -> None:
        """Register *handler* for *job_type*."""
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> TaskHandler | None:
        """Return the handler for *job_type*, or None if unregistered."""
        return self._handlers.get(job_type)

    def unregister(self, job_type: str) -> None:
        """Remove the handler for *job_type* if present."""
        self._handlers.pop(job_type, None)

    def has_handler(self, job_type: str) -> bool:
        """Return True if a handler is registered for *job_type*."""
        return job_type in self._handlers

    @property
    def job_types(self) -> list[str]:
        """Return the registered job types."""
        return list(self._handlers.keys())
