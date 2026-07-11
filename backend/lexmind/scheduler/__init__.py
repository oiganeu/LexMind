"""Scheduler -- job queue and pipeline scheduling.

Provides components for managing pipeline execution jobs:
    - Job: domain entity tracking execution state
    - JobStatus: lifecycle state enum
    - JobQueue: in-memory priority queue
    - JobExecutor: pluggable execution backend
    - JobScheduler: orchestrates the full lifecycle
    - JobRepository: persistence interface and SQLite implementation
    - PipelineDispatcher: bridges pipelines to the job queue
"""

from lexmind.scheduler.job import Job, JobStatus, can_transition
from lexmind.scheduler.job_events import (
    JobCancelled,
    JobCompleted,
    JobCreated,
    JobFailed,
    JobStarted,
)
from lexmind.scheduler.job_executor import JobExecutor
from lexmind.scheduler.job_queue import JobQueue
from lexmind.scheduler.job_repository import JobRepository, SqliteJobRepositoryImpl
from lexmind.scheduler.job_scheduler import JobScheduler
from lexmind.scheduler.pipeline_dispatcher import PipelineDispatcher

__all__ = [
    "Job",
    "JobCancelled",
    "JobCompleted",
    "JobCreated",
    "JobExecutor",
    "JobFailed",
    "JobQueue",
    "JobRepository",
    "JobScheduler",
    "JobStarted",
    "JobStatus",
    "PipelineDispatcher",
    "SqliteJobRepositoryImpl",
    "can_transition",
]
