"""Worker framework plugin.

Wraps a worker runtime as a LexMind plugin so it can be discovered, started
and stopped through the plugin framework.
"""

from __future__ import annotations

from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.workers.worker import Worker, WorkerPool


class WorkerPlugin(BasePlugin):
    """Plugin exposing the worker framework."""

    def __init__(
        self,
        worker: Worker,
        plugin_id: str = "worker",
    ) -> None:
        """Initialise the plugin with a worker runtime.

        Args:
            worker: The worker runtime (WorkerService or WorkerPool).
            plugin_id: Unique plugin identifier.
        """
        super().__init__(
            id=plugin_id,
            name="Worker Framework",
            version="1.0.0",
            description=(
                "Executes scheduled jobs via registered task handlers and "
                "emits worker-level lifecycle events."
            ),
            capabilities=(PluginCapability.WORKER,),
        )
        self._worker: Worker = worker

    @property
    def worker(self) -> Worker:
        """Return the underlying worker runtime."""
        return self._worker

    def start(self) -> None:
        """Start the worker runtime."""
        if isinstance(self._worker, WorkerPool):
            self._worker.start_all()
        else:
            self._worker.start()
        super().start()

    def stop(self) -> None:
        """Stop the worker runtime."""
        if isinstance(self._worker, WorkerPool):
            self._worker.stop_all()
        else:
            self._worker.stop()
        super().stop()
