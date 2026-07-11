"""Ingestion session model.

A session groups one or more ingestion jobs, enabling resumable and
multi-source imports under a single logical unit of work.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from lexmind.ingestion.ingestion_job import IngestionJob


@dataclass
class IngestionSession:
    """Groups related ingestion jobs for a workspace."""

    workspace_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    jobs: list[IngestionJob] = field(default_factory=list)

    def add_job(self, job: IngestionJob) -> None:
        """Attach a job to the session."""
        self.jobs.append(job)

    @property
    def is_complete(self) -> bool:
        """Return True if every job has reached a terminal state."""
        return bool(self.jobs) and all(job.is_terminal for job in self.jobs)

    @property
    def pending_jobs(self) -> list[IngestionJob]:
        """Return the jobs that have not yet reached a terminal state."""
        return [job for job in self.jobs if not job.is_terminal]
