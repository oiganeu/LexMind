"""OCR artifact writer -- persists OCR output via StorageManager.

Serialises :class:`OCRResult` instances and stores them through the
storage abstraction.  No direct filesystem access is performed; all
I/O goes through the injected ``StorageManager``.
"""

from __future__ import annotations

import json

import structlog

from lexmind.ocr.ocr_result import OCRResult

logger = structlog.get_logger(__name__)


class OCRArtifactWriter:
    """Writes OCR results to storage as text and JSON artifacts."""

    def __init__(self, storage_manager: object) -> None:
        """Initialise with a storage manager.

        Args:
            storage_manager: Façade used for all persistence.
        """
        self._storage = storage_manager

    def build_text_uri(self, workspace_id: str, document_id: str) -> str:
        """Return the storage URI for the plain-text OCR artifact."""
        return f"storage://{workspace_id}/ocr/{document_id}/text.txt"

    def build_json_uri(self, workspace_id: str, document_id: str) -> str:
        """Return the storage URI for the structured OCR artifact."""
        return f"storage://{workspace_id}/ocr/{document_id}/result.json"

    def write(
        self,
        workspace_id: str,
        document_id: str,
        result: OCRResult,
    ) -> str:
        """Persist an OCR result and return the text artifact URI.

        Writes two artifacts: a plain-text file with the recognised
        text and a JSON file with the full structured result.

        Args:
            workspace_id: The owning workspace.
            document_id: The source document.
            result: The OCR result to persist.

        Returns:
            The storage URI of the plain-text artifact.
        """
        text_uri = self.build_text_uri(workspace_id, document_id)
        json_uri = self.build_json_uri(workspace_id, document_id)

        self._storage.save_text(text_uri, result.text)  # type: ignore[union-attr]
        self._storage.save_text(  # type: ignore[union-attr]
            json_uri, self._serialize(result)
        )
        logger.info(
            "ocr_artifact_written",
            document_id=document_id,
            text_uri=text_uri,
            json_uri=json_uri,
        )
        return text_uri

    @staticmethod
    def _serialize(result: OCRResult) -> str:
        """Serialise an OCRResult to a JSON string."""
        payload = {
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language,
            "provider": result.provider,
            "page_count": result.page_count,
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "confidence": p.confidence,
                }
                for p in result.pages
            ],
            "metadata": result.metadata,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "OCRArtifactWriter()"
