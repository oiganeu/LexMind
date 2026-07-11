"""Pipeline Dispatcher -- bridges pipelines to the job queue.

Responsibilities:
    - Create jobs for pipeline runs
    - Dispatch pipelines to the scheduler
    - Map pipeline results to job results
"""

from __future__ import annotations

import structlog

from lexmind.scheduler.job import Job
from lexmind.scheduler.job_scheduler import JobScheduler

logger = structlog.get_logger(__name__)


class PipelineDispatcher:
    """Dispatches pipeline runs as jobs through the scheduler.

    Acts as a facade that translates pipeline execution requests
    into scheduler jobs, enabling asynchronous and queued pipeline
    execution.
    """

    def __init__(self, job_scheduler: JobScheduler) -> None:
        """Initialise with a job scheduler.

        Args:
            job_scheduler: The scheduler to submit pipeline jobs to.
        """
        self._scheduler = job_scheduler

    def dispatch(
        self,
        workspace_id: str,
        pipeline_id: str,
        document_id: str,
        payload: dict[str, str] | None = None,
        priority: int = 0,
    ) -> Job:
        """Submit a pipeline run as a job.

        Args:
            workspace_id: The workspace the pipeline belongs to.
            pipeline_id: The pipeline to execute.
            document_id: The document to process.
            payload: Optional additional payload.
            priority: Priority (higher = dequeued first).

        Returns:
            The created pipeline job.
        """
        job_payload = {
            "pipeline_id": pipeline_id,
            "document_id": document_id,
            **(payload or {}),
        }
        job = self._scheduler.submit(
            workspace_id=workspace_id,
            job_type="pipeline",
            payload=job_payload,
            priority=priority,
        )
        logger.info(
            "pipeline_dispatched",
            job_id=job.id,
            pipeline_id=pipeline_id,
            document_id=document_id,
        )
        return job

    def process_next_pipeline(self) -> Job | None:
        """Process the next pending pipeline job.

        Returns the executed Job, or None if the queue is empty.
        """
        return self._scheduler.process_next()

    def process_all_pipelines(self) -> list[Job]:
        """Process all pending pipeline jobs.

        Returns a list of executed jobs.
        """
        return self._scheduler.process_all()

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "PipelineDispatcher()"
