"""Job Repository -- interface and SQLite implementation.

Responsibilities:
    - CRUD operations for Job entities
    - Query pending jobs for recovery after restart
    - Track job status transitions
    - No business logic

Constraints:
    - Returns domain ``Job`` entities only.
    - No SQLAlchemy leaks outside this module.
    - Inject ``SessionManager`` via constructor.
"""

from __future__ import annotations

import json
from typing import Protocol, TypeVar, runtime_checkable

from sqlalchemy import func

from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.models import JobRow
from lexmind.scheduler.job import Job, JobStatus

T = TypeVar("T")


@runtime_checkable
class JobRepository(Protocol[T]):
    """Interface for Job persistence."""

    def create(self, job: T) -> T:
        """Persist a new job and return it."""

    def update(self, job: T) -> T:
        """Persist changes to an existing job and return it."""

    def get_by_id(self, job_id: str) -> T | None:
        """Retrieve a job by its primary key ID."""

    def list_pending(self) -> list[T]:
        """Return all jobs in PENDING status, ordered by priority."""

    def list_by_workspace(self, workspace_id: str) -> list[T]:
        """Return all jobs for a workspace."""

    def list_by_status(self, status: JobStatus) -> list[T]:
        """Return all jobs with the given status."""

    def delete(self, job_id: str) -> None:
        """Permanently remove a job from the store."""

    def exists(self, job_id: str) -> bool:
        """Return True if a job with the given ID exists."""

    def count_pending(self) -> int:
        """Return the total number of pending jobs."""


class SqliteJobRepositoryImpl:
    """SQLite-backed implementation of ``JobRepository``."""

    def __init__(self, session_manager: object) -> None:
        """Initialise with a session manager.

        Args:
            session_manager: Provides context-managed SQLAlchemy sessions.
        """
        self._sm = session_manager

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, job: Job) -> Job:
        """Persist a new job and return it."""
        row = JobRow(
            id=job.id,
            workspace_id=job.workspace_id,
            job_type=job.job_type,
            status=job.status.value,
            payload=json.dumps(job.payload),
            result=job.result,
            error_message=job.error_message,
            attempts=job.attempts,
            max_retries=job.max_retries,
            priority=job.priority,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
        )
        with self._sm.session_scope() as session:
            session.add(row)
        return job

    def update(self, job: Job) -> Job:
        """Persist changes to an existing job."""
        with self._sm.session_scope() as session:
            row = session.get(JobRow, job.id)
            if row is None:
                raise EntityNotFoundError("Job", job.id)
            row.status = job.status.value
            row.payload = json.dumps(job.payload)
            row.result = job.result
            row.error_message = job.error_message
            row.attempts = job.attempts
            row.max_retries = job.max_retries
            row.priority = job.priority
            row.started_at = job.started_at
            row.completed_at = job.completed_at
            row.updated_at = job.updated_at
        return job

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_by_id(self, job_id: str) -> Job | None:
        """Retrieve a job by its primary key ID."""
        with self._sm.session_scope() as session:
            row = session.get(JobRow, job_id)
            if row is None:
                return None
            return self._to_domain(row)

    def list_pending(self) -> list[Job]:
        """Return all PENDING jobs ordered by priority descending."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(JobRow)
                .filter(JobRow.status == JobStatus.PENDING.value)
                .order_by(JobRow.priority.desc())
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def list_by_workspace(self, workspace_id: str) -> list[Job]:
        """Return all jobs for a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(JobRow)
                .filter(JobRow.workspace_id == workspace_id)
                .order_by(JobRow.created_at.desc())
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def list_by_status(self, status: JobStatus) -> list[Job]:
        """Return all jobs with the given status."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(JobRow)
                .filter(JobRow.status == status.value)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    # ------------------------------------------------------------------
    # Delete / Existence / Count
    # ------------------------------------------------------------------

    def delete(self, job_id: str) -> None:
        """Permanently remove a job from the store."""
        with self._sm.session_scope() as session:
            row = session.get(JobRow, job_id)
            if row is None:
                raise EntityNotFoundError("Job", job_id)
            session.delete(row)

    def exists(self, job_id: str) -> bool:
        """Return True if a job with the given ID exists."""
        with self._sm.session_scope() as session:
            row = session.get(JobRow, job_id)
            return row is not None

    def count_pending(self) -> int:
        """Return the total number of pending jobs."""
        with self._sm.session_scope() as session:
            return (
                session.query(func.count())
                .select_from(JobRow)
                .filter(JobRow.status == JobStatus.PENDING.value)
                .scalar()
                or 0
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(row: JobRow) -> Job:
        """Convert an ORM row to a domain Job entity."""
        payload: dict[str, str] = json.loads(row.payload) if row.payload else {}
        return Job(
            id=row.id,
            workspace_id=row.workspace_id,
            job_type=row.job_type,
            status=JobStatus(row.status),
            payload=payload,
            result=row.result,
            error_message=row.error_message,
            attempts=row.attempts,
            max_retries=row.max_retries,
            priority=row.priority,
            created_at=row.created_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            updated_at=row.updated_at,
        )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "SqliteJobRepositoryImpl()"
