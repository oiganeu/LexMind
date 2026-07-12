"""Worker framework.

Executes scheduled jobs via registered task handlers and emits worker-level
lifecycle events. Sits on top of the Job Scheduler and Job Executor.

Public API:

- :class:`Worker` (Protocol) / :class:`WorkerService` / :class:`WorkerPool`
- :class:`TaskHandler` (Protocol) / :class:`WorkerRegistry`
- :class:`WorkerPlugin`
- Worker domain events (see :mod:`lexmind.workers.worker_events`)
"""

from lexmind.workers import worker_events
from lexmind.workers.worker import Worker, WorkerPool, WorkerService
from lexmind.workers.worker_plugin import WorkerPlugin
from lexmind.workers.worker_registry import TaskHandler, WorkerRegistry

__all__ = [
    "Worker",
    "WorkerService",
    "WorkerPool",
    "TaskHandler",
    "WorkerRegistry",
    "WorkerPlugin",
    "worker_events",
]
