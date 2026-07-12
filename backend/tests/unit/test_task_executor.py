"""Unit tests for the task executor framework (Task 30)."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.events.event_bus import EventBus
from lexmind.task_executor.task import (
    Task,
    TaskStatus,
    can_transition,
)
from lexmind.task_executor.task_events import (
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskRetriedEvent,
    TaskStartedEvent,
    TaskSubmittedEvent,
)
from lexmind.task_executor.task_executor import TaskExecutorService
from lexmind.task_executor.task_executor_exceptions import (
    InvalidTaskStateError,
    TaskHandlerNotFoundError,
)
from lexmind.task_executor.task_executor_plugin import TaskExecutorPlugin
from lexmind.task_executor.task_registry import TaskRegistry


class FakeHandler:
    """Handler that returns a fixed result or raises a fixed error."""

    def __init__(self, result: str = "ok", error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls = 0

    def execute(self, task: Task) -> str:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class FailingThenOkHandler:
    """Handler that fails until ``limit`` calls have been made."""

    def __init__(self, limit: int, error: Exception) -> None:
        self.limit = limit
        self.error = error
        self.calls = 0

    def execute(self, task: Task) -> str:
        self.calls += 1
        if self.calls <= self.limit:
            raise self.error
        return "recovered"


@dataclass
class RecordingBus(EventBus):
    """EventBus that records every published event."""

    events: list[object]

    def __init__(self) -> None:
        self.events = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def _events_of(bus: RecordingBus, cls: type) -> list[object]:
    return [e for e in bus.events if isinstance(e, cls)]


def test_task_defaults_and_identity() -> None:
    task = Task(task_type="demo")
    assert task.status is TaskStatus.PENDING
    assert task.attempts == 0
    assert task.task_id
    assert len(task.task_id) > 0


def test_task_requires_type() -> None:
    import pytest

    with pytest.raises(ValueError):
        Task(task_type="")


def test_task_transition_valid_and_invalid() -> None:
    task = Task(task_type="t")
    task.transition_to(TaskStatus.RUNNING)
    assert task.started_at is not None
    task.transition_to(TaskStatus.COMPLETED)
    assert task.completed_at is not None
    assert task.is_terminal

    bad = Task(task_type="t")
    import pytest

    with pytest.raises(InvalidTaskStateError):
        bad.transition_to(TaskStatus.COMPLETED)


def test_task_retry_semantics() -> None:
    task = Task(task_type="t", max_retries=3)
    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.FAILED)
    assert task.can_retry
    task.retry()
    assert task.status is TaskStatus.PENDING
    assert task.can_retry

    terminal = Task(task_type="t", max_retries=0)
    terminal.transition_to(TaskStatus.RUNNING)
    terminal.transition_to(TaskStatus.FAILED)
    assert not terminal.can_retry
    import pytest

    with pytest.raises(ValueError):
        terminal.retry()


def test_can_transition_matrix() -> None:
    assert can_transition(TaskStatus.PENDING, TaskStatus.RUNNING)
    assert can_transition(TaskStatus.PENDING, TaskStatus.CANCELLED)
    assert can_transition(TaskStatus.RUNNING, TaskStatus.FAILED)
    assert can_transition(TaskStatus.FAILED, TaskStatus.PENDING)
    assert not can_transition(TaskStatus.COMPLETED, TaskStatus.RUNNING)
    assert not can_transition(TaskStatus.CANCELLED, TaskStatus.PENDING)


def test_registry_register_and_lookup() -> None:
    registry = TaskRegistry()
    handler = FakeHandler()
    registry.register("a", handler)
    assert registry.has("a")
    assert registry.get("a") is handler
    assert registry.registered_types() == ["a"]


def test_registry_rejects_bad_args() -> None:
    registry = TaskRegistry()
    import pytest

    with pytest.raises(ValueError):
        registry.register("", FakeHandler())
    with pytest.raises(ValueError):
        registry.register("x", None)


def test_registry_missing_handler() -> None:
    import pytest

    with pytest.raises(TaskHandlerNotFoundError):
        TaskRegistry().get("missing")


def test_executor_success_emits_events() -> None:
    registry = TaskRegistry()
    registry.register("ok", FakeHandler(result="done"))
    bus = RecordingBus()
    executor = TaskExecutorService(registry, bus)
    task = Task(task_type="ok")
    result = executor.execute(task)

    assert result.status is TaskStatus.COMPLETED
    assert result.result == "done"
    assert result.attempts == 1
    assert _events_of(bus, TaskSubmittedEvent)
    assert len(_events_of(bus, TaskStartedEvent)) == 1
    completed = _events_of(bus, TaskCompletedEvent)
    assert len(completed) == 1
    assert completed[0].result == "done"
    assert completed[0].attempts == 1


def test_executor_failure_no_retry() -> None:
    registry = TaskRegistry()
    registry.register("bad", FakeHandler(error=RuntimeError("boom")))
    bus = RecordingBus()
    executor = TaskExecutorService(registry, bus)
    task = Task(task_type="bad", max_retries=0)
    result = executor.execute(task)

    assert result.status is TaskStatus.FAILED
    assert "boom" in result.error_message
    assert result.attempts == 1
    failed = _events_of(bus, TaskFailedEvent)
    assert len(failed) == 1
    assert "boom" in failed[0].error_message


def test_executor_retries_then_succeeds() -> None:
    registry = TaskRegistry()
    handler = FailingThenOkHandler(limit=2, error=RuntimeError("transient"))
    registry.register("flaky", handler)
    bus = RecordingBus()
    delays: list[float] = []
    executor = TaskExecutorService(registry, bus, delay=delays.append)
    task = Task(task_type="flaky", max_retries=3)
    result = executor.execute(task)

    assert result.status is TaskStatus.COMPLETED
    assert result.attempts == 3
    assert handler.calls == 3
    assert len(_events_of(bus, TaskRetriedEvent)) == 2
    assert len(delays) == 2


def test_executor_retries_exhausted() -> None:
    registry = TaskRegistry()
    handler = FailingThenOkHandler(limit=10, error=RuntimeError("always"))
    registry.register("flaky", handler)
    bus = RecordingBus()
    executor = TaskExecutorService(registry, bus)
    task = Task(task_type="flaky", max_retries=2)
    result = executor.execute(task)

    assert result.status is TaskStatus.FAILED
    assert result.attempts == 3
    assert len(_events_of(bus, TaskRetriedEvent)) == 2
    assert len(_events_of(bus, TaskFailedEvent)) == 1


def test_executor_missing_handler_raises() -> None:
    bus = RecordingBus()
    executor = TaskExecutorService(TaskRegistry(), bus)
    import pytest

    with pytest.raises(TaskHandlerNotFoundError):
        executor.execute(Task(task_type="ghost"))
    assert _events_of(bus, TaskSubmittedEvent)


def test_executor_rejects_non_pending() -> None:
    registry = TaskRegistry()
    registry.register("ok", FakeHandler())
    executor = TaskExecutorService(registry)
    running = Task(task_type="ok")
    running.transition_to(TaskStatus.RUNNING)
    import pytest

    with pytest.raises(InvalidTaskStateError):
        executor.execute(running)


def test_executor_cancel() -> None:
    registry = TaskRegistry()
    registry.register("ok", FakeHandler())
    bus = RecordingBus()
    executor = TaskExecutorService(registry, bus)
    task = Task(task_type="ok")
    cancelled = executor.cancel(task)

    assert cancelled.status is TaskStatus.CANCELLED
    events = _events_of(bus, TaskCancelledEvent)
    assert len(events) == 1
    assert events[0].previous_status is TaskStatus.PENDING


def test_executor_cancel_terminal_raises() -> None:
    registry = TaskRegistry()
    registry.register("ok", FakeHandler())
    bus = RecordingBus()
    executor = TaskExecutorService(registry, bus)
    task = Task(task_type="ok", max_retries=0)
    executor.execute(task)
    import pytest

    with pytest.raises(InvalidTaskStateError):
        executor.cancel(task)


def test_executor_batch() -> None:
    registry = TaskRegistry()
    registry.register("ok", FakeHandler(result="r"))
    executor = TaskExecutorService(registry)
    results = executor.execute_batch([Task(task_type="ok"), Task(task_type="ok")])
    assert all(r.status is TaskStatus.COMPLETED for r in results)
    assert len(results) == 2


def test_plugin_wires_up() -> None:
    bus = RecordingBus()
    plugin = TaskExecutorPlugin(bus)
    assert plugin.registry is not None
    assert plugin.executor is not None
    plugin.register_handler("ok", FakeHandler(result="x"))
    assert plugin.registry.has("ok")
    plugin.start()
    plugin.stop()
