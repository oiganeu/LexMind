"""OCR artifact generator -- orchestrates persistence and registration.

Given an :class:`OCRResult`, produces the three standardised artifact
payloads, persists them through the ``StorageManager`` abstraction, and
registers the primary artifact via the ``OCRArtifactRepositoryAdapter``.

The generator is independent of any OCR engine and performs no direct
filesystem access -- all persistence goes through the storage facade.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.ocr.artifacts.ocr_artifact_repository_adapter import (
    OCRArtifactRepositoryAdapter,
)
from lexmind.ocr.artifacts.ocr_artifact_serializer import OCRArtifactSerializer
from lexmind.ocr.ocr_result import OCRResult

logger = structlog.get_logger(__name__)

TEXT_FILENAME = "ocr_text.txt"
RESULT_FILENAME = "ocr_result.json"
METADATA_FILENAME = "ocr_metadata.json"

TEXT_MEDIA_TYPE = "text/plain"
JSON_MEDIA_TYPE = "application/json"


@dataclass(frozen=True, slots=True)
class OCRArtifactSet:
    """Summary of the artifacts produced for a single OCR run."""

    artifact_id: str
    version: int
    text_uri: str
    result_uri: str
    metadata_uri: str
    text_checksum: str
    result_checksum: str
    metadata_checksum: str


class OCRArtifactGenerator:
    """Generates, persists and registers standardised OCR artifacts."""

    def __init__(
        self,
        storage_manager: object,
        repository_adapter: OCRArtifactRepositoryAdapter,
        serializer: OCRArtifactSerializer | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialise with collaborators.

        Args:
            storage_manager: Facade used for all persistence.
            repository_adapter: Registers artifacts with the repository.
            serializer: Converts results to payloads; a default is used
                when omitted.
            clock: Supplies the generation timestamp; injected for
                deterministic testing.
        """
        self._storage = storage_manager
        self._adapter = repository_adapter
        self._serializer = serializer or OCRArtifactSerializer()
        self._clock = clock or (lambda: datetime.now(UTC))

    def build_uri(
        self, workspace_id: str, document_id: str, filename: str
    ) -> str:
        """Return the storage URI for an OCR artifact file."""
        return f"storage://{workspace_id}/artifacts/ocr/{document_id}/{filename}"

    def generate(
        self,
        workspace_id: str,
        document_id: str,
        result: OCRResult,
        producer_module: str = "ocr",
        producer_version: str = "",
    ) -> OCRArtifactSet:
        """Generate, persist and register OCR artifacts for *result*.

        Args:
            workspace_id: Owning workspace identifier.
            document_id: Source document identifier.
            result: The OCR result to persist.
            producer_module: Name of the producing module.
            producer_version: Version of the producing module.

        Returns:
            An :class:`OCRArtifactSet` describing the persisted artifacts.
        """
        text_uri = self.build_uri(workspace_id, document_id, TEXT_FILENAME)
        result_uri = self.build_uri(workspace_id, document_id, RESULT_FILENAME)
        metadata_uri = self.build_uri(workspace_id, document_id, METADATA_FILENAME)

        text_payload = self._serializer.serialize_text(result)
        result_payload = self._serializer.serialize_result(result)
        metadata_payload = self._serializer.serialize_metadata(
            result, document_id, generated_at=self._clock()
        )

        text_checksum = self._serializer.checksum(text_payload)
        result_checksum = self._serializer.checksum(result_payload)
        metadata_checksum = self._serializer.checksum(metadata_payload)

        self._save(text_uri, text_payload)
        self._save(result_uri, result_payload)
        self._save(metadata_uri, metadata_payload)

        artifact = self._register(
            workspace_id=workspace_id,
            document_id=document_id,
            text_uri=text_uri,
            result_uri=result_uri,
            metadata_uri=metadata_uri,
            text_checksum=text_checksum,
            result_checksum=result_checksum,
            metadata_checksum=metadata_checksum,
            producer_module=producer_module,
            producer_version=producer_version,
        )

        logger.info(
            "ocr_artifacts_generated",
            document_id=document_id,
            artifact_id=artifact.id,
            version=artifact.current_version,
        )

        return OCRArtifactSet(
            artifact_id=artifact.id,
            version=artifact.current_version,
            text_uri=text_uri,
            result_uri=result_uri,
            metadata_uri=metadata_uri,
            text_checksum=text_checksum,
            result_checksum=result_checksum,
            metadata_checksum=metadata_checksum,
        )

    def _save(self, uri: str, payload: str) -> None:
        """Persist *payload* to *uri* through the storage facade."""
        self._storage.save_text(uri, payload)  # type: ignore[union-attr]

    def _register(
        self,
        *,
        workspace_id: str,
        document_id: str,
        text_uri: str,
        result_uri: str,
        metadata_uri: str,
        text_checksum: str,
        result_checksum: str,
        metadata_checksum: str,
        producer_module: str,
        producer_version: str,
    ) -> Artifact:
        """Register the primary OCR text artifact with sidecar metadata."""
        extra = {
            "result_uri": result_uri,
            "result_checksum": result_checksum,
            "metadata_uri": metadata_uri,
            "metadata_checksum": metadata_checksum,
        }
        return self._adapter.register(
            workspace_id=workspace_id,
            document_id=document_id,
            storage_uri=text_uri,
            checksum=text_checksum,
            media_type=TEXT_MEDIA_TYPE,
            artifact_type=ArtifactType.OCR_TEXT,
            producer_module=producer_module,
            producer_version=producer_version,
            extra=extra,
        )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "OCRArtifactGenerator()"
