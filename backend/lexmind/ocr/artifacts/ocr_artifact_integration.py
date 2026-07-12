"""OCR artifact integration service.

Orchestrates storing, retrieving, finding and deleting OCR artifacts.
Publishes lifecycle events on the injected :class:`~lexmind.events.event_bus.EventBus`
and enforces overwrite semantics through
:class:`~lexmind.ocr.artifacts.artifact_types.OcrArtifactOptions`.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.ocr.artifacts.artifact_repository import (
    ArtifactRepository,
    DuplicateArtifactError,
)
from lexmind.ocr.artifacts.artifact_types import (
    OcrArtifact,
    OcrArtifactOptions,
    OcrArtifactQuery,
)
from lexmind.ocr.artifacts.ocr_artifact_events import (
    OcrArtifactDeleted,
    OcrArtifactFailed,
    OcrArtifactStored,
)

logger = structlog.get_logger(__name__)


class OcrArtifactIntegrationService:
    """Service layer for OCR artifact integration.

    Delegates persistence to an injected :class:`ArtifactRepository` and
    publishes lifecycle events on an optional :class:`EventBus`.
    """

    def __init__(
        self,
        repository: ArtifactRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialise with a repository and optional event bus.

        Args:
            repository: Backing store for OCR artifacts.
            event_bus: Optional bus for lifecycle events.
        """
        if repository is None:
            raise ValueError("repository must not be None")
        self._repository = repository
        self._event_bus = event_bus

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def store(
        self,
        artifact: OcrArtifact,
        options: OcrArtifactOptions | None = None,
    ) -> None:
        """Store an OCR artifact.

        Args:
            artifact: The artifact to persist.
            options: Behavioural options; defaults to no-overwrite.

        Raises:
            DuplicateArtifactError: If *artifact* already exists and
                overwrite is not permitted.
        """
        opts = options or OcrArtifactOptions()
        try:
            self._repository.save(artifact, overwrite=opts.allows_overwrite())
            self._emit(
                OcrArtifactStored(
                    artifact_id=artifact.artifact_id,
                    document_id=artifact.document_id,
                    page_number=artifact.page_number,
                )
            )
            logger.info(
                "ocr_artifact_stored",
                artifact_id=artifact.artifact_id,
                document_id=artifact.document_id,
            )
        except DuplicateArtifactError:
            self._emit(
                OcrArtifactFailed(
                    artifact_id=artifact.artifact_id,
                    error_message=f"Duplicate artifact '{artifact.artifact_id}'",
                )
            )
            logger.warning(
                "ocr_artifact_duplicate",
                artifact_id=artifact.artifact_id,
            )
            raise

    def get(self, artifact_id: str) -> OcrArtifact | None:
        """Return the artifact with *artifact_id* or ``None``."""
        return self._repository.get(artifact_id)

    def find(self, query: OcrArtifactQuery) -> list[OcrArtifact]:
        """Return artifacts matching *query*."""
        return self._repository.find(query)

    def delete(self, artifact_id: str) -> bool:
        """Delete an artifact; return True if it existed.

        Publishes :class:`OcrArtifactDeleted` on success.
        """
        removed = self._repository.delete(artifact_id)
        if removed:
            self._emit(
                OcrArtifactDeleted(
                    artifact_id=artifact_id,
                )
            )
            logger.info("ocr_artifact_deleted", artifact_id=artifact_id)
        return removed

    def list_all(self) -> list[OcrArtifact]:
        """Return every stored artifact."""
        return self._repository.list_all()
