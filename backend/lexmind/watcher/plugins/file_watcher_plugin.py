"""File Watcher plugin.

Wraps :class:`FileWatcherService` as a LexMind plugin so the watcher
can be discovered, started and stopped through the plugin framework.
"""

from __future__ import annotations

from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.watcher.event_dispatcher import EventDispatcher
from lexmind.watcher.file_watcher import FileWatcher, FileWatcherService
from lexmind.watcher.watch_backend import WatchBackend


class FileWatcherPlugin(BasePlugin):
    """Plugin exposing the file watcher framework."""

    def __init__(
        self,
        backend: WatchBackend,
        dispatcher: EventDispatcher,
        plugin_id: str = "file-watcher",
    ) -> None:
        """Initialise the plugin with its backend and dispatcher.

        Args:
            backend: Pluggable backend used to detect raw changes.
            dispatcher: Delivers emitted ``FileEvent`` instances.
            plugin_id: Unique plugin identifier.
        """
        super().__init__(
            id=plugin_id,
            name="File Watcher",
            version="1.0.0",
            description="Monitors configured directories and emits file events.",
            capabilities=(PluginCapability.FILE_WATCH,),
        )
        self._service: FileWatcher = FileWatcherService(backend, dispatcher)

    @property
    def service(self) -> FileWatcher:
        """Return the underlying file watcher service."""
        return self._service

    def stop(self) -> None:
        """Stop every active watch and flush buffered events."""
        for watch_id in self._service.watching_ids():
            self._service.stop(watch_id)
        super().stop()
