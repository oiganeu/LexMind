"""Worker framework.

A worker is the runtime that drives job execution.  It pulls pending jobs
from a :class:`JobScheduler`, ensures the right :class:`TaskHandler` is
registered with the scheduler's executor, and emits worker-level lifecycle
events.  A :class:`WorkerPool` coordinates multiple workers for concurrency.

The framework depends only on the ``JobScheduler`` and ``JobExecutor``
collaborators (injected) and an optional EventBus.  It performs no I/O of its
own; all persistence and execution are delegated.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog

from lexmind.scheduler.job import Job, JobStatus
from lexmind.scheduler.job_executor import JobExecutor
from lexmind.scheduler.job_scheduler import JobScheduler
from lexmind.workers import worker_events as events
from lexmind.workers.worker_registry import TaskHandler, WorkerRegistry

logger = structlog.get_logger(__name__)


@runtime_checkable
class Worker(Protocol):
    """Public contract of a worker runtime."""

    def register(self, job_type: str, handler: TaskHandler) -> None:
        """Register a task handler for *job_type*."""
        ...

    def run_once(self) -> Job | None:
        """Execute a single pending job, or return None if the queue is empty."""
        ...

    def run_all(self) -> list[Job]:
        """Execute all pending jobs currently in the queue."""
        ...

    def start(self) -> None:
        """Mark the worker as running and emit ``WorkerStarted``."""
        ...

    def stop(self) -> None:
        """Mark the worker as stopped and emit ``WorkerStopped``."""
        ...

    @property
    def is_running(self) -> bool:
        """Return True while the worker runtime is active."""
        ...


class WorkerService:
    """Default :class:`Worker` implementation.

    Args:
        scheduler: Source of pending jobs (also performs execution).
        executor: Receiver of task handlers (shared with *scheduler*).
        registry: Registry of task handlers by job type.
        worker_id: Stable identifier for this worker.
        event_bus: Optional bus for worker-level events (noop when None).
    """

    def __init__(
        self,
        scheduler: JobScheduler,
        executor: JobExecutor,
        registry: WorkerRegistry,
        worker_id: str = "worker",
        event_bus: object | None = None,
    ) -> None:
        self._scheduler = scheduler
        self._executor = executor
        self._registry = registry
        self._worker_id = worker_id
        self._bus = event_bus
        self._running = False

    def register(self, job_type: str, handler: TaskHandler) -> None:
        """Register *handler* for *job_type* on both registry and executor."""
        self._registry.register(job_type, handler)
        self._executor.register(job_type, handler)

    def run_once(self) -> Job | None:
        """Execute a single pending job, or return None if queue is empty."""
        try:
            job = self._scheduler.process_next()
        except Exception as exc:  # noqa: BLE001 - surface as worker failure
            logger.error("worker_job_error", worker_id=self._worker_id, error=str(exc))
            self._emit(
                events.TaskFailed(job_id="", job_type="", error_message=str(exc))
            )
            return None
        if job is None:
            return None
        self._emit(
            events.TaskAssigned(
                job_id=job.id,
                job_type=job.job_type,
                workspace_id=job.workspace_id,
            )
        )
        if job.status == JobStatus.FAILED:
            self._emit(
                events.TaskFailed(
                    job_id=job.id,
                    job_type=job.job_type,
                    error_message=job.error_message,
                )
            )
        else:
            self._emit(
                events.TaskCompleted(
                    job_id=job.id,
                    job_type=job.job_type,
                    result=job.result,
                )
            )
        return job

    def run_all(self) -> list[Job]:
        """Execute all pending jobs currently in the queue."""
        results: list[Job] = []
        while True:
            job = self.run_once()
            if job is None:
                break
            results.append(job)
        return results

    def start(self) -> None:
        """Mark the worker as running and emit ``WorkerStarted``."""
        self._running = True
        self._emit(events.WorkerStarted(worker_id=self._worker_id))

    def stop(self) -> None:
        """Mark the worker as stopped and emit ``WorkerStopped``."""
        self._running = False
        self._emit(events.WorkerStopped(worker_id=self._worker_id))

    @property
    def is_running(self) -> bool:
        """Return True while the worker runtime is active."""
        return self._running

    @property
    def worker_id(self) -> str:
        """Return this worker's identifier."""
        return self._worker_id

    def _emit(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._bus is not None:
            self._bus.publish(event)  # type: ignore[attr-defined]


class WorkerPool:
    """Coordinates multiple :class:`WorkerService` instances.

    Args:
        scheduler: Shared job scheduler.
        executor: Shared job executor.
        registry: Shared handler registry.
        event_bus: Optional event bus.
        pool_size: Number of worker runtimes to manage.
        worker_id_prefix: Prefix for per-worker identifiers.
    """

    def __init__(
        self,
        scheduler: JobScheduler,
        executor: JobExecutor,
        registry: WorkerRegistry,
        event_bus: object | None = None,
        pool_size: int = 1,
        worker_id_prefix: str = "worker",
    ) -> None:
        if pool_size < 1:
            raise ValueError("pool_size must be >= 1")
        self._scheduler = scheduler
        self._executor = executor
        self._registry = registry
        self._bus = event_bus
        self._pool_size = pool_size
        self._prefix = worker_id_prefix
        self._workers: list[WorkerService] = [
            WorkerService(
                scheduler=scheduler,
                executor=executor,
                registry=registry,
                worker_id=f"{worker_id_prefix}-{i}",
                event_bus=event_bus,
            )
            for i in range(pool_size)
        ]
        self._next = 0

    def register(self, job_type: str, handler: TaskHandler) -> None:
        """Register *handler* for *job_type* across all workers."""
        self._registry.register(job_type, handler)
        self._executor.register(job_type, handler)

    def run_once(self) -> Job | None:
        """Execute one job on the next worker in round-robin order."""
        worker = self._workers[self._next]
        self._next = (self._next + 1) % len(self._workers)
        return worker.run_once()

    def run_all(self) -> list[Job]:
        """Execute all pending jobs across the pool."""
        return self._workers[0].run_all()

    def start_all(self) -> None:
        """Start every worker in the pool."""
        for worker in self._workers:
            worker.start()

    def stop_all(self) -> None:
        """Stop every worker in the pool."""
        for worker in self._workers:
            worker.stop()

    @property
    def size(self) -> int:
        """Return the number of workers in the pool."""
        return len(self._workers)

    @property
    def is_running(self) -> bool:
        """Return True if any worker in the pool is running."""
        return any(w.is_running for w in self._workers)
