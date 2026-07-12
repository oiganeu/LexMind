"""Tests for the Worker Framework (TASK-0029).

Covers:
    - WorkerService: register, run_once, run_all, start/stop, events
    - WorkerPool: pool_size validation, round-robin, start/stop all
    - WorkerRegistry / TaskHandler
    - WorkerPlugin lifecycle
    - Event emission (and no-op when bus is None)
"""

from __future__ import annotations

import pytest

from lexmind.scheduler import JobExecutor, JobQueue, JobScheduler
from lexmind.scheduler.job import Job, JobStatus
from lexmind.scheduler.job_repository import JobRepository
from lexmind.workers import (
    WorkerPlugin,
    WorkerPool,
    WorkerRegistry,
    WorkerService,
)
from lexmind.workers import worker_events as events

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeEventBus:
    """Records published events."""

    def __init__(self) -> None:
        self.published: list[object] = []

    def publish(self, event: object) -> None:
        self.published.append(event)


class InMemoryJobRepository:
    """Minimal in-memory JobRepository for worker tests."""

    def __init__(self) -> None:
        self._store: dict[str, Job] = {}

    def create(self, job: Job) -> Job:
        self._store[job.id] = job
        return job

    def update(self, job: Job) -> Job:
        self._store[job.id] = job
        return job

    def get_by_id(self, job_id: str) -> Job | None:
        return self._store.get(job_id)

    def delete(self, job_id: str) -> None:
        self._store.pop(job_id, None)

    def list_pending(
        self, workspace_id: str | None = None, priority: int | None = None
    ) -> list[Job]:
        return [
            j
            for j in self._store.values()
            if j.status == JobStatus.PENDING
            and (workspace_id is None or j.workspace_id == workspace_id)
            and (priority is None or j.priority == priority)
        ]

    def count_pending(self) -> int:
        return sum(1 for j in self._store.values() if j.status == JobStatus.PENDING)

    def get_queued(self, workspace_id: str) -> list[Job]:
        return [
            j
            for j in self._store.values()
            if j.workspace_id == workspace_id
            and j.status in (JobStatus.PENDING, JobStatus.RUNNING)
        ]


def _stack(
    bus: FakeEventBus | None = None,
) -> tuple[JobScheduler, JobExecutor, WorkerRegistry, FakeEventBus]:
    """Build a scheduler + executor + registry wired for worker tests."""
    repo: JobRepository = InMemoryJobRepository()
    queue = JobQueue(repo)
    executor = JobExecutor(repo, event_bus=bus)
    scheduler = JobScheduler(queue, executor, repo, event_bus=bus)
    registry = WorkerRegistry()
    return scheduler, executor, registry, bus or FakeEventBus()


# ---------------------------------------------------------------------------
# WorkerRegistry / TaskHandler
# ---------------------------------------------------------------------------


class TestWorkerRegistry:
    def test_register_and_get(self) -> None:
        reg = WorkerRegistry()

        def h(job: Job) -> str:
            return "ok"

        reg.register("t", h)
        assert reg.get("t") is h
        assert reg.has_handler("t")
        assert "t" in reg.job_types

    def test_unknown_handler_none(self) -> None:
        reg = WorkerRegistry()
        assert reg.get("x") is None
        assert not reg.has_handler("x")

    def test_unregister(self) -> None:
        reg = WorkerRegistry()

        def h(job: Job) -> str:
            return "ok"

        reg.register("t", h)
        reg.unregister("t")
        assert not reg.has_handler("t")


# ---------------------------------------------------------------------------
# WorkerService
# ---------------------------------------------------------------------------


class TestWorkerService:
    def _service(self, bus=None) -> WorkerService:
        scheduler, executor, registry, bus = _stack(bus)
        return WorkerService(scheduler, executor, registry, event_bus=bus)

    def test_register_stores_in_registry_and_executor(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)

        def handler(job: Job) -> str:
            return "done"

        svc.register("ingest", handler)
        assert registry.has_handler("ingest")
        assert executor.has_handler("ingest")

    def test_run_once_empty_returns_none(self) -> None:
        svc = self._service()
        assert svc.run_once() is None

    def test_run_once_executes_and_emits(self) -> None:
        bus = FakeEventBus()
        scheduler, executor, registry, _ = _stack(bus)
        svc = WorkerService(scheduler, executor, registry, event_bus=bus)

        def handler(job: Job) -> str:
            return f"ran {job.id}"

        svc.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest", payload={"k": "v"})
        job = svc.run_once()
        assert job is not None
        assert job.status == JobStatus.COMPLETED
        assert job.result == f"ran {job.id}"
        types = [type(e) for e in bus.published]
        assert events.TaskAssigned in types
        assert events.TaskCompleted in types

    def test_run_once_failure_emits_task_failed(self) -> None:
        bus = FakeEventBus()
        scheduler, executor, registry, _ = _stack(bus)
        svc = WorkerService(scheduler, executor, registry, event_bus=bus)

        def handler(job: Job) -> str:
            raise RuntimeError("boom")

        svc.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest")
        job = svc.run_once()
        assert job is not None
        assert job.status == JobStatus.FAILED
        assert any(
            isinstance(e, events.TaskFailed) and e.job_id == job.id
            for e in bus.published
        )

    def test_run_all_drains_queue(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)

        def handler(job: Job) -> str:
            return "ok"

        svc.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest")
        scheduler.submit("ws1", job_type="ingest")
        results = svc.run_all()
        assert len(results) == 2
        assert all(r.status == JobStatus.COMPLETED for r in results)

    def test_start_stop_toggles_running(self) -> None:
        bus = FakeEventBus()
        svc = self._service(bus)
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        assert any(isinstance(e, events.WorkerStarted) for e in bus.published)
        svc.stop()
        assert not svc.is_running
        assert any(isinstance(e, events.WorkerStopped) for e in bus.published)

    def test_no_bus_noop(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)

        def handler(job: Job) -> str:
            return "ok"

        svc.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest")
        svc.start()
        job = svc.run_once()
        svc.stop()
        assert job is not None
        assert job.status == JobStatus.COMPLETED

    def test_run_once_no_handler_emits_failure(self) -> None:
        bus = FakeEventBus()
        scheduler, executor, registry, _ = _stack(bus)
        svc = WorkerService(scheduler, executor, registry, event_bus=bus)
        scheduler.submit("ws1", job_type="unknown")
        result = svc.run_once()
        assert result is None
        assert any(
            isinstance(e, events.TaskFailed) and e.error_message
            for e in bus.published
        )

    def test_worker_id_property(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(
            scheduler, executor, registry, worker_id="w-7"
        )
        assert svc.worker_id == "w-7"


# ---------------------------------------------------------------------------
# WorkerPool
# ---------------------------------------------------------------------------


class TestWorkerPool:
    def test_pool_size_minimum(self) -> None:
        scheduler, executor, registry, _ = _stack()
        with pytest.raises(ValueError):
            WorkerPool(scheduler, executor, registry, pool_size=0)

    def test_size_and_register(self) -> None:
        scheduler, executor, registry, _ = _stack()
        pool = WorkerPool(scheduler, executor, registry, pool_size=3)
        assert pool.size == 3

        def handler(job: Job) -> str:
            return "ok"

        pool.register("ingest", handler)
        assert registry.has_handler("ingest")

    def test_start_stop_all(self) -> None:
        bus = FakeEventBus()
        scheduler, executor, registry, _ = _stack(bus)
        pool = WorkerPool(scheduler, executor, registry, event_bus=bus, pool_size=2)
        assert not pool.is_running
        pool.start_all()
        assert pool.is_running
        pool.stop_all()
        assert not pool.is_running

    def test_run_once_round_robin(self) -> None:
        bus = FakeEventBus()
        scheduler, executor, registry, _ = _stack(bus)
        pool = WorkerPool(scheduler, executor, registry, event_bus=bus, pool_size=2)

        def handler(job: Job) -> str:
            return "ok"

        pool.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest")
        scheduler.submit("ws1", job_type="ingest")
        first = pool.run_once()
        second = pool.run_once()
        assert first is not None
        assert second is not None

    def test_run_all(self) -> None:
        scheduler, executor, registry, _ = _stack()
        pool = WorkerPool(scheduler, executor, registry, pool_size=2)

        def handler(job: Job) -> str:
            return "ok"

        pool.register("ingest", handler)
        scheduler.submit("ws1", job_type="ingest")
        scheduler.submit("ws1", job_type="ingest")
        results = pool.run_all()
        assert len(results) == 2


# ---------------------------------------------------------------------------
# WorkerPlugin
# ---------------------------------------------------------------------------


class TestWorkerPlugin:
    def test_plugin_capability(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)
        plugin = WorkerPlugin(worker=svc)
        assert plugin.metadata.capabilities[0].value == "worker"

    def test_plugin_starts_worker(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)
        plugin = WorkerPlugin(worker=svc)
        plugin.initialize(context=None)
        plugin.start()
        assert svc.is_running
        plugin.stop()
        assert not svc.is_running

    def test_plugin_with_pool(self) -> None:
        scheduler, executor, registry, _ = _stack()
        pool = WorkerPool(scheduler, executor, registry, pool_size=2)
        plugin = WorkerPlugin(worker=pool)
        plugin.initialize(context=None)
        plugin.start()
        assert pool.is_running
        plugin.stop()
        assert not pool.is_running

    def test_plugin_exposes_worker(self) -> None:
        scheduler, executor, registry, _ = _stack()
        svc = WorkerService(scheduler, executor, registry)
        plugin = WorkerPlugin(worker=svc)
        assert plugin.worker is svc
