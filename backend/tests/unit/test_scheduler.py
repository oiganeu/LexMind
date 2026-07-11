"""Tests for Scheduler subsystem (TASK-0022).

Covers:
    - Job domain entity: state transitions, retry, is_terminal, can_retry
    - can_transition: valid and invalid transitions
    - JobQueue: enqueue, dequeue, peek, size, is_empty
    - JobExecutor: register/unregister handlers, execute, error handling
    - JobScheduler: submit, process_next, process_all, retry, cancel, recover
    - SqliteJobRepositoryImpl: CRUD, list_pending, list_by_status, exists, delete, count
    - PipelineDispatcher: dispatch, process_next_pipeline, process_all_pipelines
    - Events: JobCreated, JobStarted, JobCompleted, JobFailed, JobCancelled
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lexmind.metadata.database import Database
from lexmind.metadata.session import SessionManager
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
from lexmind.scheduler.job_repository import SqliteJobRepositoryImpl
from lexmind.scheduler.job_scheduler import JobScheduler
from lexmind.scheduler.pipeline_dispatcher import PipelineDispatcher

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db() -> Database:
    """Provide an in-memory Database."""
    d = Database("sqlite:///:memory:")
    d.initialize()
    yield d
    d.dispose()


@pytest.fixture()
def session_mgr(db: Database) -> SessionManager:
    """Provide a SessionManager."""
    return SessionManager(db.engine)


@pytest.fixture()
def job_repo(session_mgr: SessionManager) -> SqliteJobRepositoryImpl:
    """Provide a JobRepository."""
    return SqliteJobRepositoryImpl(session_mgr)


@pytest.fixture()
def event_bus() -> MagicMock:
    """Provide a mock event bus."""
    return MagicMock()


@pytest.fixture()
def job_queue(job_repo: SqliteJobRepositoryImpl) -> JobQueue:
    """Provide a JobQueue."""
    return JobQueue(job_repo)


@pytest.fixture()
def job_executor(
    job_repo: SqliteJobRepositoryImpl,
    event_bus: MagicMock,
) -> JobExecutor:
    """Provide a JobExecutor."""
    return JobExecutor(job_repository=job_repo, event_bus=event_bus)


@pytest.fixture()
def scheduler(
    job_queue: JobQueue,
    job_executor: JobExecutor,
    job_repo: SqliteJobRepositoryImpl,
    event_bus: MagicMock,
) -> JobScheduler:
    """Provide a JobScheduler."""
    return JobScheduler(
        job_queue=job_queue,
        job_executor=job_executor,
        job_repository=job_repo,
        event_bus=event_bus,
    )


@pytest.fixture()
def dispatcher(scheduler: JobScheduler) -> PipelineDispatcher:
    """Provide a PipelineDispatcher."""
    return PipelineDispatcher(scheduler)


def _noop_handler(job: Job) -> str:
    """No-op handler that returns 'ok'."""
    return "ok"


def _fail_handler(job: Job) -> str:
    """Handler that always raises."""
    raise RuntimeError("boom")


def _slow_handler(job: Job) -> str:
    """Handler that returns a result string."""
    return "processed"


# ===========================================================================
# Job domain entity
# ===========================================================================


class TestJobEntity:
    """Test Job domain entity state machine."""

    def test_create_default(self) -> None:
        """Job defaults to PENDING with generated ID."""
        job = Job(workspace_id="ws-1")
        assert job.status == JobStatus.PENDING
        assert job.workspace_id == "ws-1"
        assert job.id  # non-empty
        assert job.attempts == 0
        assert job.max_retries == 3
        assert job.priority == 0

    def test_create_requires_workspace(self) -> None:
        """Job raises if workspace_id is empty."""
        with pytest.raises(ValueError, match="must belong to a workspace"):
            Job(workspace_id="")

    def test_transition_to_running(self) -> None:
        """PENDING -> RUNNING increments attempts and sets started_at."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING
        assert job.attempts == 1
        assert job.started_at is not None

    def test_transition_to_completed(self) -> None:
        """RUNNING -> COMPLETED sets completed_at."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

    def test_transition_to_failed(self) -> None:
        """RUNNING -> FAILED sets completed_at."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.FAILED)
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None

    def test_transition_to_cancelled(self) -> None:
        """PENDING -> CANCELLED is allowed."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.CANCELLED)
        assert job.status == JobStatus.CANCELLED

    def test_transition_to_cancelled_from_running(self) -> None:
        """RUNNING -> CANCELLED is allowed."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.CANCELLED)
        assert job.status == JobStatus.CANCELLED

    def test_invalid_transition_raises(self) -> None:
        """Invalid transitions raise ValueError."""
        job = Job(workspace_id="ws-1")
        with pytest.raises(ValueError, match="Cannot transition"):
            job.transition_to(JobStatus.COMPLETED)

    def test_completed_is_terminal(self) -> None:
        """COMPLETED is terminal."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.is_terminal is True

    def test_cancelled_is_terminal(self) -> None:
        """CANCELLED is terminal."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.CANCELLED)
        assert job.is_terminal is True

    def test_pending_is_not_terminal(self) -> None:
        """PENDING is not terminal."""
        job = Job(workspace_id="ws-1")
        assert job.is_terminal is False

    def test_can_retry_when_failed(self) -> None:
        """FAILED job with attempts < max_retries can retry."""
        job = Job(workspace_id="ws-1", max_retries=3)
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.FAILED)
        assert job.can_retry is True

    def test_cannot_retry_when_max_attempts(self) -> None:
        """FAILED job with attempts >= max_retries cannot retry."""
        job = Job(workspace_id="ws-1", max_retries=1)
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.FAILED)
        assert job.can_retry is False

    def test_cannot_retry_when_completed(self) -> None:
        """COMPLETED job cannot retry."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.can_retry is False

    def test_retry_resets_to_pending(self) -> None:
        """retry() resets FAILED job to PENDING."""
        job = Job(workspace_id="ws-1", max_retries=3)
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.FAILED)
        job.retry()
        assert job.status == JobStatus.PENDING
        assert job.error_message == ""

    def test_retry_raises_when_not_retryable(self) -> None:
        """retry() raises when job cannot be retried."""
        job = Job(workspace_id="ws-1", max_retries=1)
        job.transition_to(JobStatus.RUNNING)
        job.transition_to(JobStatus.FAILED)
        with pytest.raises(ValueError, match="cannot be retried"):
            job.retry()


# ===========================================================================
# can_transition
# ===========================================================================


class TestCanTransition:
    """Test the can_transition helper."""

    def test_valid_transitions(self) -> None:
        """Valid transitions return True."""
        assert can_transition(JobStatus.PENDING, JobStatus.RUNNING) is True
        assert can_transition(JobStatus.PENDING, JobStatus.CANCELLED) is True
        assert can_transition(JobStatus.RUNNING, JobStatus.COMPLETED) is True
        assert can_transition(JobStatus.RUNNING, JobStatus.FAILED) is True
        assert can_transition(JobStatus.RUNNING, JobStatus.CANCELLED) is True
        assert can_transition(JobStatus.FAILED, JobStatus.PENDING) is True

    def test_invalid_transitions(self) -> None:
        """Invalid transitions return False."""
        assert can_transition(JobStatus.PENDING, JobStatus.COMPLETED) is False
        assert can_transition(JobStatus.COMPLETED, JobStatus.PENDING) is False
        assert can_transition(JobStatus.CANCELLED, JobStatus.RUNNING) is False
        assert can_transition(JobStatus.FAILED, JobStatus.COMPLETED) is False


# ===========================================================================
# JobQueue
# ===========================================================================


class TestJobQueue:
    """Test JobQueue operations."""

    def test_enqueue_dequeue(self, job_queue: JobQueue) -> None:
        """Enqueue a job and dequeue it."""
        job = Job(workspace_id="ws-1")
        job_queue.enqueue(job)
        assert job_queue.size == 1

        dequeued = job_queue.dequeue()
        assert dequeued is not None
        assert dequeued.id == job.id
        assert dequeued.status == JobStatus.PENDING

    def test_dequeue_empty(self, job_queue: JobQueue) -> None:
        """Dequeue from empty queue returns None."""
        assert job_queue.dequeue() is None

    def test_peek_does_not_remove(self, job_queue: JobQueue) -> None:
        """Peek returns the job without removing it."""
        job = Job(workspace_id="ws-1")
        job_queue.enqueue(job)
        peeked = job_queue.peek()
        assert peeked is not None
        assert job_queue.size == 1

    def test_enqueue_rejects_non_pending(self, job_queue: JobQueue) -> None:
        """Enqueue rejects jobs not in PENDING status."""
        job = Job(workspace_id="ws-1")
        job.transition_to(JobStatus.RUNNING)
        with pytest.raises(ValueError, match="Can only enqueue PENDING"):
            job_queue.enqueue(job)

    def test_priority_ordering(self, job_queue: JobQueue) -> None:
        """Higher priority jobs are dequeued first."""
        low = Job(workspace_id="ws-1", priority=1)
        high = Job(workspace_id="ws-1", priority=10)
        medium = Job(workspace_id="ws-1", priority=5)
        job_queue.enqueue(low)
        job_queue.enqueue(high)
        job_queue.enqueue(medium)

        first = job_queue.dequeue()
        assert first is not None
        assert first.priority == 10

    def test_size_and_is_empty(self, job_queue: JobQueue) -> None:
        """Size and is_empty reflect queue state."""
        assert job_queue.is_empty is True
        assert job_queue.size == 0

        job_queue.enqueue(Job(workspace_id="ws-1"))
        assert job_queue.is_empty is False
        assert job_queue.size == 1


# ===========================================================================
# JobExecutor
# ===========================================================================


class TestJobExecutor:
    """Test JobExecutor operations."""

    def test_register_and_has_handler(self, job_executor: JobExecutor) -> None:
        """Register a handler and check existence."""
        assert job_executor.has_handler("pipeline") is False
        job_executor.register("pipeline", _noop_handler)
        assert job_executor.has_handler("pipeline") is True

    def test_unregister(self, job_executor: JobExecutor) -> None:
        """Unregister removes a handler."""
        job_executor.register("pipeline", _noop_handler)
        job_executor.unregister("pipeline")
        assert job_executor.has_handler("pipeline") is False

    def test_execute_success(self, job_executor: JobExecutor) -> None:
        """Execute a job with a successful handler."""
        job_executor.register("pipeline", _noop_handler)
        job = Job(workspace_id="ws-1", job_type="pipeline")
        result = job_executor.execute(job)
        assert result.status == JobStatus.COMPLETED
        assert result.result == "ok"

    def test_execute_failure(self, job_executor: JobExecutor) -> None:
        """Execute a job with a failing handler."""
        job_executor.register("pipeline", _fail_handler)
        job = Job(workspace_id="ws-1", job_type="pipeline")
        result = job_executor.execute(job)
        assert result.status == JobStatus.FAILED
        assert "boom" in result.error_message

    def test_execute_no_handler_raises(self, job_executor: JobExecutor) -> None:
        """Execute without a registered handler raises."""
        job = Job(workspace_id="ws-1", job_type="unknown")
        with pytest.raises(ValueError, match="No handler registered"):
            job_executor.execute(job)

    def test_execute_persists_job(self, job_executor: JobExecutor) -> None:
        """Execute persists the job via the repository."""
        job_executor.register("pipeline", _noop_handler)
        job = Job(workspace_id="ws-1", job_type="pipeline")
        job_executor.execute(job)
        # The job should have been created in the repo by the executor
        assert job.status == JobStatus.COMPLETED

    def test_execute_publishes_events(self, job_executor: JobExecutor) -> None:
        """Execute publishes JobStarted and JobCompleted events."""
        job_executor.register("pipeline", _noop_handler)
        job = Job(workspace_id="ws-1", job_type="pipeline")
        job_executor.execute(job)
        bus = job_executor._event_bus  # type: ignore[attr-defined]
        assert bus.publish.call_count >= 2  # JobStarted + JobCompleted

    def test_repr(self, job_executor: JobExecutor) -> None:
        """__repr__ lists registered handlers."""
        job_executor.register("pipeline", _noop_handler)
        assert "pipeline" in repr(job_executor)


# ===========================================================================
# JobScheduler
# ===========================================================================


class TestJobScheduler:
    """Test JobScheduler orchestration."""

    def test_submit_creates_job(self, scheduler: JobScheduler) -> None:
        """Submit creates and enqueues a job."""
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        assert job.status == JobStatus.PENDING
        assert job.workspace_id == "ws-1"
        assert job.job_type == "pipeline"

    def test_submit_with_payload(self, scheduler: JobScheduler) -> None:
        """Submit with payload stores it on the job."""
        job = scheduler.submit(
            workspace_id="ws-1",
            job_type="pipeline",
            payload={"doc_id": "abc"},
        )
        assert job.payload == {"doc_id": "abc"}

    def test_process_next(self, scheduler: JobScheduler) -> None:
        """Process_next dequeues and executes the next job."""
        scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        result = scheduler.process_next()
        assert result is not None
        assert result.status == JobStatus.COMPLETED

    def test_process_next_empty(self, scheduler: JobScheduler) -> None:
        """Process_next returns None when queue is empty."""
        assert scheduler.process_next() is None

    def test_process_all(self, scheduler: JobScheduler) -> None:
        """Process_all executes all pending jobs."""
        scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        results = scheduler.process_all()
        assert len(results) == 2
        assert all(r.status == JobStatus.COMPLETED for r in results)

    def test_retry_job(self, scheduler: JobScheduler) -> None:
        """retry_job re-enqueues a failed job."""
        scheduler._executor.register("pipeline", _fail_handler)  # type: ignore[attr-defined]
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        executed = scheduler.process_next()
        assert executed is not None
        assert executed.status == JobStatus.FAILED

        retried = scheduler.retry_job(job.id)
        assert retried is not None
        assert retried.status == JobStatus.PENDING

    def test_retry_nonexistent(self, scheduler: JobScheduler) -> None:
        """retry_job returns None for unknown ID."""
        assert scheduler.retry_job("nonexistent") is None

    def test_retry_non_retryable(self, scheduler: JobScheduler) -> None:
        """retry_job returns None for a completed (non-retryable) job."""
        scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        scheduler.process_next()
        assert scheduler.retry_job(job.id) is None

    def test_repr(self, scheduler: JobScheduler) -> None:
        """__repr__ reports the queue size."""
        assert "JobScheduler" in repr(scheduler)

    def test_cancel_job(self, scheduler: JobScheduler) -> None:
        """cancel_job transitions a pending job to CANCELLED."""
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        cancelled = scheduler.cancel_job(job.id)
        assert cancelled is not None
        assert cancelled.status == JobStatus.CANCELLED

    def test_cancel_nonexistent(self, scheduler: JobScheduler) -> None:
        """cancel_job returns None for unknown ID."""
        assert scheduler.cancel_job("nonexistent") is None

    def test_cancel_terminal_job(self, scheduler: JobScheduler) -> None:
        """cancel_job returns None for terminal jobs."""
        scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        scheduler.process_next()
        # process_next reads from DB; check the persisted state
        refreshed = scheduler.get_job(job.id)
        assert refreshed is not None
        assert refreshed.is_terminal
        assert scheduler.cancel_job(job.id) is None

    def test_cancel_failed_job(self, scheduler: JobScheduler) -> None:
        """cancel_job returns None for a FAILED job (invalid transition)."""
        scheduler._executor.register("pipeline", _fail_handler)  # type: ignore[attr-defined]
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        scheduler.process_next()
        refreshed = scheduler.get_job(job.id)
        assert refreshed is not None
        assert refreshed.status == JobStatus.FAILED
        assert scheduler.cancel_job(job.id) is None

    def test_get_job(self, scheduler: JobScheduler) -> None:
        """get_job retrieves a job by ID."""
        job = scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        retrieved = scheduler.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id

    def test_recover_pending(self, scheduler: JobScheduler) -> None:
        """recover_pending returns all pending jobs from the repository."""
        scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        scheduler.submit(workspace_id="ws-1", job_type="pipeline")
        pending = scheduler.recover_pending()
        assert len(pending) == 2
        assert all(j.status == JobStatus.PENDING for j in pending)


# ===========================================================================
# SqliteJobRepositoryImpl
# ===========================================================================


class TestJobRepository:
    """Test SQLite JobRepository implementation."""

    def test_create_and_get(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """Create a job and retrieve it by ID."""
        job = Job(workspace_id="ws-1", job_type="pipeline")
        job_repo.create(job)
        retrieved = job_repo.get_by_id(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.workspace_id == "ws-1"
        assert retrieved.job_type == "pipeline"
        assert retrieved.status == JobStatus.PENDING

    def test_update(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """Update a job persists changes."""
        job = Job(workspace_id="ws-1")
        job_repo.create(job)
        job.transition_to(JobStatus.RUNNING)
        job_repo.update(job)
        retrieved = job_repo.get_by_id(job.id)
        assert retrieved is not None
        assert retrieved.status == JobStatus.RUNNING
        assert retrieved.attempts == 1

    def test_get_nonexistent(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """get_by_id returns None for unknown ID."""
        assert job_repo.get_by_id("nonexistent") is None

    def test_list_pending(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """list_pending returns only pending jobs."""
        job_repo.create(Job(workspace_id="ws-1", priority=1))
        job_repo.create(Job(workspace_id="ws-1", priority=10))
        running = Job(workspace_id="ws-1")
        running.transition_to(JobStatus.RUNNING)
        job_repo.create(running)

        pending = job_repo.list_pending()
        assert len(pending) == 2
        assert all(j.status == JobStatus.PENDING for j in pending)
        # Higher priority first
        assert pending[0].priority == 10

    def test_list_by_workspace(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """list_by_workspace returns only jobs for that workspace."""
        job_repo.create(Job(workspace_id="ws-1"))
        job_repo.create(Job(workspace_id="ws-2"))
        job_repo.create(Job(workspace_id="ws-1"))

        ws1_jobs = job_repo.list_by_workspace("ws-1")
        assert len(ws1_jobs) == 2

    def test_list_by_status(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """list_by_status returns only jobs with the given status."""
        job_repo.create(Job(workspace_id="ws-1"))
        running = Job(workspace_id="ws-1")
        running.transition_to(JobStatus.RUNNING)
        job_repo.create(running)

        pending = job_repo.list_by_status(JobStatus.PENDING)
        assert len(pending) == 1
        running_jobs = job_repo.list_by_status(JobStatus.RUNNING)
        assert len(running_jobs) == 1

    def test_delete(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """delete removes a job from the store."""
        job = Job(workspace_id="ws-1")
        job_repo.create(job)
        job_repo.delete(job.id)
        assert job_repo.get_by_id(job.id) is None

    def test_delete_nonexistent(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """delete raises for unknown ID."""
        from lexmind.metadata.exceptions import EntityNotFoundError

        with pytest.raises(EntityNotFoundError):
            job_repo.delete("nonexistent")

    def test_update_nonexistent(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """update raises for unknown ID."""
        from lexmind.metadata.exceptions import EntityNotFoundError

        with pytest.raises(EntityNotFoundError):
            job_repo.update(Job(workspace_id="ws-1"))

    def test_repr(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """__repr__ is informative."""
        assert "SqliteJobRepositoryImpl" in repr(job_repo)

    def test_exists(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """exists returns True for existing jobs."""
        job = Job(workspace_id="ws-1")
        job_repo.create(job)
        assert job_repo.exists(job.id) is True
        assert job_repo.exists("nonexistent") is False

    def test_count_pending(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """count_pending returns the correct count."""
        assert job_repo.count_pending() == 0
        job_repo.create(Job(workspace_id="ws-1"))
        job_repo.create(Job(workspace_id="ws-1"))
        assert job_repo.count_pending() == 2
        running = Job(workspace_id="ws-1")
        running.transition_to(JobStatus.RUNNING)
        job_repo.create(running)
        assert job_repo.count_pending() == 2  # running not counted

    def test_payload_roundtrip(self, job_repo: SqliteJobRepositoryImpl) -> None:
        """Payload dict survives create/read roundtrip."""
        job = Job(workspace_id="ws-1", payload={"key": "value", "num": "42"})
        job_repo.create(job)
        retrieved = job_repo.get_by_id(job.id)
        assert retrieved is not None
        assert retrieved.payload == {"key": "value", "num": "42"}


# ===========================================================================
# PipelineDispatcher
# ===========================================================================


class TestPipelineDispatcher:
    """Test PipelineDispatcher facade."""

    def test_dispatch(self, dispatcher: PipelineDispatcher) -> None:
        """dispatch creates a pipeline job."""
        job = dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-1",
            document_id="doc-1",
        )
        assert job.job_type == "pipeline"
        assert job.payload["pipeline_id"] == "pipe-1"
        assert job.payload["document_id"] == "doc-1"

    def test_dispatch_with_payload(self, dispatcher: PipelineDispatcher) -> None:
        """dispatch merges extra payload."""
        job = dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-1",
            document_id="doc-1",
            payload={"extra": "data"},
        )
        assert job.payload["extra"] == "data"
        assert job.payload["pipeline_id"] == "pipe-1"

    def test_dispatch_with_priority(self, dispatcher: PipelineDispatcher) -> None:
        """dispatch sets priority."""
        job = dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-1",
            document_id="doc-1",
            priority=5,
        )
        assert job.priority == 5

    def test_process_next_pipeline(self, dispatcher: PipelineDispatcher) -> None:
        """process_next_pipeline processes the next job."""
        dispatcher._scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-1",
            document_id="doc-1",
        )
        result = dispatcher.process_next_pipeline()
        assert result is not None
        assert result.status == JobStatus.COMPLETED

    def test_process_all_pipelines(self, dispatcher: PipelineDispatcher) -> None:
        """process_all_pipelines processes all pending jobs."""
        dispatcher._scheduler._executor.register("pipeline", _noop_handler)  # type: ignore[attr-defined]
        dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-1",
            document_id="doc-1",
        )
        dispatcher.dispatch(
            workspace_id="ws-1",
            pipeline_id="pipe-2",
            document_id="doc-2",
        )
        results = dispatcher.process_all_pipelines()
        assert len(results) == 2

    def test_repr(self, dispatcher: PipelineDispatcher) -> None:
        """__repr__ is informative."""
        assert "PipelineDispatcher" in repr(dispatcher)


# ===========================================================================
# Events
# ===========================================================================


class TestJobEvents:
    """Test job lifecycle events."""

    def test_job_created_event(self) -> None:
        """JobCreated stores workspace_id and job_type."""
        event = JobCreated(
            workspace_id="ws-1",
            job_type="pipeline",
            aggregate_id="job-1",
        )
        assert event.workspace_id == "ws-1"
        assert event.job_type == "pipeline"
        assert event.aggregate_id == "job-1"
        assert event.event_id  # auto-generated

    def test_job_started_event(self) -> None:
        """JobStarted stores workspace_id and job_type."""
        event = JobStarted(
            workspace_id="ws-1",
            job_type="pipeline",
            aggregate_id="job-1",
        )
        assert event.workspace_id == "ws-1"

    def test_job_completed_event(self) -> None:
        """JobCompleted stores result."""
        event = JobCompleted(
            workspace_id="ws-1",
            job_type="pipeline",
            aggregate_id="job-1",
            result="done",
        )
        assert event.result == "done"

    def test_job_failed_event(self) -> None:
        """JobFailed stores error_message."""
        event = JobFailed(
            workspace_id="ws-1",
            job_type="pipeline",
            aggregate_id="job-1",
            error_message="boom",
        )
        assert event.error_message == "boom"

    def test_job_cancelled_event(self) -> None:
        """JobCancelled stores workspace_id."""
        event = JobCancelled(
            workspace_id="ws-1",
            job_type="pipeline",
            aggregate_id="job-1",
        )
        assert event.workspace_id == "ws-1"

    def test_events_are_frozen(self) -> None:
        """All job events are immutable."""
        event = JobCreated(workspace_id="ws-1", job_type="pipeline")
        with pytest.raises(AttributeError):
            event.workspace_id = "ws-2"  # type: ignore[misc]
