"""Task executor plugin.

The :class:`TaskExecutorPlugin` exposes the task executor capability and
owns a :class:`TaskExecutorService` plus the :class:`TaskRegistry` used to
dispatch tasks to handlers contributed by other plugins.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.task_executor.task_executor import TaskExecutor, TaskExecutorService
from lexmind.task_executor.task_registry import TaskHandler, TaskRegistry


class TaskExecutorPlugin(BasePlugin):
    """Plugin that provides resilient task execution."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        super().__init__(
            id="task_executor",
            name="Task Executor",
            version="1.0.0",
            description="Resilient task execution engine with retries.",
            capabilities=(PluginCapability.TASK_EXECUTOR,),
        )
        self._registry = TaskRegistry()
        self._executor: TaskExecutor = TaskExecutorService(self._registry, event_bus)

    @property
    def registry(self) -> TaskRegistry:
        """Return the task registry."""
        return self._registry

    @property
    def executor(self) -> TaskExecutor:
        """Return the task executor."""
        return self._executor

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        """Register a task handler contributed by another plugin."""
        self._registry.register(task_type, handler)

    def start(self) -> None:
        """Activate the plugin (the executor is stateless)."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
