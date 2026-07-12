"""Import Queue plugin.

Wraps :class:`ImportQueueService` as a LexMind plugin so the import queue can
be discovered, started and stopped through the plugin framework.
"""

from __future__ import annotations

from lexmind.import_queue.import_queue import ImportQueue
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class ImportQueuePlugin(BasePlugin):
    """Plugin exposing the import queue framework."""

    def __init__(
        self,
        service: ImportQueue,
        plugin_id: str = "import-queue",
    ) -> None:
        """Initialise the plugin with its queue service.

        Args:
            service: The ImportQueueService instance.
            plugin_id: Unique plugin identifier.
        """
        super().__init__(
            id=plugin_id,
            name="Import Queue",
            version="1.0.0",
            description=(
                "Coordinates import requests with priority, "
                "deduplication, and job submission."
            ),
            capabilities=(PluginCapability.IMPORT_QUEUE,),
        )
        self._service: ImportQueue = service

    @property
    def service(self) -> ImportQueue:
        """Return the underlying import queue service."""
        return self._service

    def stop(self) -> None:
        """Cancel any pending requests and flush the queue."""
        for req_id in self._service.pending_ids():
            self._service.cancel(req_id)
        super().stop()
