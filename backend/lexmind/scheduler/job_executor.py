"""Job Executor -- runs job callables in a pluggable backend.

Responsibilities:
    - Execute a callable for a given Job
    - Handle exceptions and update job status
    - Support pluggable backends (in-process, thread pool, etc.)
"""

from __future__ import annotations

from collections.abc import Callable

import structlog

from lexmind.scheduler.job import Job, JobStatus
from lexmind.scheduler.job_events import JobCompleted, JobFailed, JobStarted

logger = structlog.get_logger(__name__)

# Type alias for job handlers -- receives a Job, returns a result string.
JobHandler = Callable[[Job], str]


class JobExecutor:
    """Executes jobs by dispatching to registered handlers.

    The executor delegates actual work to registered ``JobHandler``
    callables.  Execution backend (thread pool, asyncio, etc.) is
    determined by the caller; this class stays synchronous.
    """

    def __init__(
        self,
        job_repository: object | None = None,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with optional collaborators.

        Args:
            job_repository: Persistence layer for status updates.
            event_bus: Optional event bus for lifecycle events.
        """
        self._repo = job_repository
        self._event_bus = event_bus
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_type: str, handler: JobHandler) -> None:
        """Register a handler for a given job type.

        Args:
            job_type: The job_type string to match.
            handler: Callable that receives a Job and returns a result.
        """
        self._handlers[job_type] = handler

    def unregister(self, job_type: str) -> None:
        """Remove a handler for a given job type."""
        self._handlers.pop(job_type, None)

    def has_handler(self, job_type: str) -> bool:
        """Return True if a handler is registered for the given type."""
        return job_type in self._handlers

    def execute(self, job: Job) -> Job:
        """Execute a job and return the updated Job.

        Transitions the job to RUNNING, calls the handler, then
        transitions to COMPLETED or FAILED.

        Args:
            job: The job to execute.

        Returns:
            The updated Job entity.

        Raises:
            ValueError: If no handler is registered for the job type.
        """
        if job.job_type not in self._handlers:
            raise ValueError(
                f"No handler registered for job_type={job.job_type!r}"
            )

        # Transition to RUNNING
        job.transition_to(JobStatus.RUNNING)
        self._emit(JobStarted(
            aggregate_id=job.id,
            workspace_id=job.workspace_id,
            job_type=job.job_type,
        ))
        self._persist(job)

        # Execute handler
        handler = self._handlers[job.job_type]
        try:
            result = handler(job)
            job.result = result or ""
            job.transition_to(JobStatus.COMPLETED)
            self._emit(JobCompleted(
                aggregate_id=job.id,
                workspace_id=job.workspace_id,
                job_type=job.job_type,
                result=job.result,
            ))
        except Exception as exc:
            job.error_message = str(exc)
            job.transition_to(JobStatus.FAILED)
            self._emit(JobFailed(
                aggregate_id=job.id,
                workspace_id=job.workspace_id,
                job_type=job.job_type,
                error_message=job.error_message,
            ))
            logger.error(
                "job_execution_failed",
                job_id=job.id,
                job_type=job.job_type,
                error=job.error_message,
            )

        self._persist(job)
        return job

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]

    def _persist(self, job: Job) -> None:
        """Persist job state if repository is available."""
        if self._repo is not None:
            existing = self._repo.get_by_id(job.id)  # type: ignore[union-attr]
            if existing is not None:
                self._repo.update(job)  # type: ignore[union-attr]
            else:
                self._repo.create(job)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"JobExecutor(handlers={list(self._handlers.keys())})"
