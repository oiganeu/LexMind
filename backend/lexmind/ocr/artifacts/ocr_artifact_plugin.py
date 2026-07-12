"""OCR artifact integration plugin.

Exposes the OCR artifact integration framework through the plugin system.
Wraps an :class:`~lexmind.ocr.artifacts.ocr_artifact_integration.OcrArtifactIntegrationService`
backed by an
:class:`~lexmind.ocr.artifacts.artifact_repository.InMemoryArtifactRepository`
and declares :class:`~lexmind.plugins.plugin_capability.PluginCapability.OCR_ARTIFACT_INTEGRATION`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.artifacts.artifact_repository import (
    ArtifactRepository,
    ArtifactRepositoryRegistry,
    InMemoryArtifactRepository,
)
from lexmind.ocr.artifacts.artifact_types import (
    OcrArtifact,
    OcrArtifactOptions,
    OcrArtifactQuery,
)
from lexmind.ocr.artifacts.ocr_artifact_integration import (
    OcrArtifactIntegrationService,
)
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OcrArtifactIntegrationPlugin(BasePlugin):
    """Plugin providing OCR artifact integration."""

    def __init__(
        self,
        repository: ArtifactRepository | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "ocr-artifact-integration",
    ) -> None:
        """Initialise the plugin.

        Args:
            repository: Backing store for OCR artifacts.  Defaults to a
                fresh :class:`InMemoryArtifactRepository`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="OCR Artifact Integration",
            version="1.0.0",
            description="Associates OCR output with document artifacts "
            "such as pages, images and regions.",
            capabilities=(PluginCapability.OCR_ARTIFACT_INTEGRATION,),
        )
        self._repository = repository or InMemoryArtifactRepository()
        self._registry = ArtifactRepositoryRegistry()
        self._event_bus = event_bus
        self._service = OcrArtifactIntegrationService(
            self._repository, event_bus=event_bus
        )

    @property
    def service(self) -> OcrArtifactIntegrationService:
        """Return the underlying integration service."""
        return self._service

    @property
    def artifact_repository(self) -> ArtifactRepository:
        """Return the default artifact repository."""
        return self._repository

    @property
    def registry(self) -> ArtifactRepositoryRegistry:
        """Return the repository registry."""
        return self._registry

    def store(
        self,
        artifact: OcrArtifact,
        options: OcrArtifactOptions | None = None,
    ) -> None:
        """Store an OCR artifact via the service."""
        self._service.store(artifact, options)

    def get(self, artifact_id: str) -> OcrArtifact | None:
        """Retrieve an artifact by id."""
        return self._service.get(artifact_id)

    def find(self, query: OcrArtifactQuery) -> list[OcrArtifact]:
        """Find artifacts matching *query*."""
        return self._service.find(query)

    def delete(self, artifact_id: str) -> bool:
        """Delete an artifact; return True if it existed."""
        return self._service.delete(artifact_id)

    def list_all(self) -> list[OcrArtifact]:
        """Return every stored artifact."""
        return self._service.list_all()

    def register_repository(self, name: str, repo: ArtifactRepository) -> None:
        """Register a named repository in the registry."""
        self._registry.register(name, repo)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
