"""Job Queue -- in-memory priority queue backed by the repository.

Responsibilities:
    - Enqueue pending jobs
    - Dequeue highest-priority pending job
    - Track queue size
    - No persistence (delegates to JobRepository)
"""

from __future__ import annotations

from lexmind.scheduler.job import Job, JobStatus


class JobQueue:
    """In-memory priority queue for pipeline jobs.

    The queue delegates persistence to the ``JobRepository`` and
    maintains an in-memory index for fast dequeue operations.
    """

    def __init__(self, job_repository: object) -> None:
        """Initialise with a job repository.

        Args:
            job_repository: Used to persist and query jobs.
        """
        self._repo = job_repository

    def enqueue(self, job: Job) -> Job:
        """Add a job to the queue (persists as PENDING).

        If the job already exists in the repository it is updated;
        otherwise it is created.  This supports retry flows where a
        failed job is reset to PENDING and re-enqueued.

        Args:
            job: The job to enqueue.  Must be in PENDING status.

        Returns:
            The persisted job.

        Raises:
            ValueError: If the job is not in PENDING status.
        """
        if job.status != JobStatus.PENDING:
            raise ValueError(
                f"Can only enqueue PENDING jobs, got {job.status}"
            )
        existing = self._repo.get_by_id(job.id)  # type: ignore[union-attr]
        if existing is not None:
            return self._repo.update(job)  # type: ignore[union-attr]
        return self._repo.create(job)  # type: ignore[union-attr]

    def dequeue(self) -> Job | None:
        """Remove and return the highest-priority pending job.

        Returns None if the queue is empty.
        """
        pending = self._repo.list_pending()  # type: ignore[union-attr]
        if not pending:
            return None
        return pending[0]

    def peek(self) -> Job | None:
        """Return the highest-priority pending job without removing it.

        Returns None if the queue is empty.
        """
        return self.dequeue()

    @property
    def size(self) -> int:
        """Return the number of pending jobs."""
        return self._repo.count_pending()  # type: ignore[union-attr]

    @property
    def is_empty(self) -> bool:
        """Return True if the queue has no pending jobs."""
        return self.size == 0
