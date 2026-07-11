"""OCR artifact serialiser -- converts OCR results to storable payloads.

Produces three standardised representations of an :class:`OCRResult`:

* ``ocr_text.txt``     -- the plain recognised text.
* ``ocr_result.json``  -- the full structured recognition result.
* ``ocr_metadata.json`` -- descriptive metadata about the OCR run.

The serialiser is independent of any OCR engine and performs no I/O; it
only transforms domain value objects into strings.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from lexmind.ocr.ocr_result import OCRResult


class OCRArtifactSerializer:
    """Serialises :class:`OCRResult` instances into artifact payloads."""

    def serialize_text(self, result: OCRResult) -> str:
        """Return the plain-text representation of *result*."""
        return result.text

    def serialize_result(self, result: OCRResult) -> str:
        """Return the full structured JSON representation of *result*."""
        payload = {
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language,
            "provider": result.provider,
            "page_count": result.page_count,
            "pages": [
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "confidence": page.confidence,
                }
                for page in result.pages
            ],
            "metadata": result.metadata,
        }
        return self._dump(payload)

    def serialize_metadata(
        self,
        result: OCRResult,
        document_id: str,
        generated_at: datetime | None = None,
    ) -> str:
        """Return descriptive JSON metadata about the OCR run.

        Args:
            result: The OCR result being described.
            document_id: The source document identifier.
            generated_at: Timestamp of generation (defaults to now, UTC).
        """
        timestamp = generated_at or datetime.now(UTC)
        payload = {
            "document_id": document_id,
            "provider": result.provider,
            "language": result.language,
            "confidence": result.confidence,
            "page_count": result.page_count,
            "character_count": len(result.text),
            "is_empty": result.is_empty,
            "generated_at": timestamp.isoformat(),
        }
        return self._dump(payload)

    @staticmethod
    def checksum(payload: str, algorithm: str = "sha256") -> str:
        """Return the hex digest of *payload* computed in memory.

        No filesystem access is performed; this operates purely on the
        serialised string so callers do not depend on storage internals.
        """
        digest = hashlib.new(algorithm)
        digest.update(payload.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def _dump(payload: dict[str, object]) -> str:
        """Serialise *payload* to a stable JSON string."""
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "OCRArtifactSerializer()"
