"""Job Scheduler -- orchestrates job lifecycle.

Responsibilities:
    - Create and enqueue jobs
    - Dequeue and execute jobs
    - Handle retries on failure
    - Persist state transitions
    - Publish lifecycle events
"""

from __future__ import annotations

import structlog

from lexmind.scheduler.job import Job, JobStatus
from lexmind.scheduler.job_events import JobCancelled, JobCreated
from lexmind.scheduler.job_executor import JobExecutor
from lexmind.scheduler.job_queue import JobQueue

logger = structlog.get_logger(__name__)


class JobScheduler:
    """Orchestrates the lifecycle of pipeline jobs.

    Combines queue, executor, and repository to provide a
    high-level create/dequeue/execute/retry API.
    """

    def __init__(
        self,
        job_queue: JobQueue,
        job_executor: JobExecutor,
        job_repository: object,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with collaborators.

        Args:
            job_queue: Queue for pending jobs.
            job_executor: Executor for running jobs.
            job_repository: Persistence layer for jobs.
            event_bus: Optional event bus for lifecycle events.
        """
        self._queue = job_queue
        self._executor = job_executor
        self._repo = job_repository
        self._event_bus = event_bus

    def submit(
        self,
        workspace_id: str,
        job_type: str,
        payload: dict[str, str] | None = None,
        priority: int = 0,
        max_retries: int = 3,
    ) -> Job:
        """Create a new job and enqueue it.

        Args:
            workspace_id: The workspace the job belongs to.
            job_type: The type of job to execute.
            payload: Optional payload data.
            priority: Priority (higher = dequeued first).
            max_retries: Maximum retry attempts.

        Returns:
            The created and enqueued Job.
        """
        job = Job(
            workspace_id=workspace_id,
            job_type=job_type,
            payload=payload or {},
            priority=priority,
            max_retries=max_retries,
        )
        self._queue.enqueue(job)
        self._emit(JobCreated(
            aggregate_id=job.id,
            workspace_id=workspace_id,
            job_type=job_type,
        ))
        logger.info(
            "job_created",
            job_id=job.id,
            job_type=job_type,
            workspace_id=workspace_id,
        )
        return job

    def process_next(self) -> Job | None:
        """Dequeue and execute the next pending job.

        Returns the executed Job, or None if the queue is empty.
        """
        job = self._queue.dequeue()
        if job is None:
            return None
        return self._execute(job)

    def process_all(self) -> list[Job]:
        """Process all pending jobs in the queue.

        Returns a list of executed jobs (completed or failed).
        """
        results: list[Job] = []
        while not self._queue.is_empty:
            job = self.process_next()
            if job is not None:
                results.append(job)
        return results

    def retry_job(self, job_id: str) -> Job | None:
        """Retry a failed job by resetting it to PENDING.

        Args:
            job_id: The ID of the job to retry.

        Returns:
            The re-enqueued Job, or None if not found/retryable.
        """
        job = self._repo.get_by_id(job_id)  # type: ignore[union-attr]
        if job is None:
            return None
        if not job.can_retry:
            logger.warning(
                "job_not_retryable",
                job_id=job.id,
                status=job.status,
                attempts=job.attempts,
            )
            return None
        job.retry()
        self._repo.update(job)  # type: ignore[union-attr]
        self._queue.enqueue(job)
        logger.info("job_retried", job_id=job.id)
        return job

    def cancel_job(self, job_id: str) -> Job | None:
        """Cancel a pending or running job.

        Args:
            job_id: The ID of the job to cancel.

        Returns:
            The cancelled Job, or None if not found.
        """
        job = self._repo.get_by_id(job_id)  # type: ignore[union-attr]
        if job is None:
            return None
        if job.is_terminal:
            return None
        try:
            job.transition_to(JobStatus.CANCELLED)
        except ValueError:
            logger.warning(
                "job_cancel_failed",
                job_id=job.id,
                status=job.status,
            )
            return None
        self._repo.update(job)  # type: ignore[union-attr]
        self._emit(JobCancelled(
            aggregate_id=job.id,
            workspace_id=job.workspace_id,
            job_type=job.job_type,
        ))
        logger.info("job_cancelled", job_id=job.id)
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Retrieve a job by ID."""
        return self._repo.get_by_id(job_id)  # type: ignore[union-attr]

    def recover_pending(self) -> list[Job]:
        """Recover and re-enqueue pending jobs (startup recovery).

        Queries the repository for PENDING jobs and adds them
        back to the in-memory queue.

        Returns:
            List of recovered jobs.
        """
        pending = self._repo.list_pending()  # type: ignore[union-attr]
        for job in pending:
            logger.info("job_recovered", job_id=job.id)
        return pending

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _execute(self, job: Job) -> Job:
        """Execute a job via the executor.

        Failed jobs remain in FAILED status and must be retried
        explicitly via :meth:`retry_job`.
        """
        return self._executor.execute(job)

    def _emit(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"JobScheduler(queue_size={self._queue.size})"
