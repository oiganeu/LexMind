"""OCR provider interface.

Defines the contract every OCR engine plugin must satisfy.  Concrete
engines (Tesseract, PaddleOCR, cloud OCR) are implemented in separate
plugins; this module contains only the abstraction so the orchestration
layer stays engine-agnostic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lexmind.ocr.ocr_result import OCRResult


@runtime_checkable
class OCRProvider(Protocol):
    """Contract for OCR engine plugins."""

    @property
    def name(self) -> str:
        """Return the unique provider name (e.g. ``tesseract``)."""
        ...

    def supports(self, mime_type: str) -> bool:
        """Return True if the provider can process the given MIME type."""
        ...

    def recognize(
        self,
        image_data: bytes,
        language: str = "",
        mime_type: str = "",
    ) -> OCRResult:
        """Run OCR on *image_data* and return an :class:`OCRResult`.

        Args:
            image_data: Raw bytes of the image or PDF to recognise.
            language: Optional language hint (e.g. ``ron``, ``eng``).
            mime_type: Optional MIME type of the input.

        Returns:
            The recognition result.
        """
        ...
