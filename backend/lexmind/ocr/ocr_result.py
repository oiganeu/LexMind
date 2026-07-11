"""OCR result value object.

Represents the outcome of an OCR recognition run.  Independent of any
specific OCR engine so it can be produced by Tesseract, PaddleOCR, or a
cloud provider alike.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OCRPageResult:
    """Recognition result for a single page or image region."""

    page_number: int = 0
    text: str = ""
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Aggregate OCR output for a document.

    Attributes:
        text: The full recognised text (all pages concatenated).
        confidence: Overall confidence in the range [0.0, 1.0].
        language: Detected or requested language code.
        provider: Name of the provider that produced the result.
        pages: Per-page results.
        metadata: Provider-specific extra data (opaque to the pipeline).
    """

    text: str = ""
    confidence: float = 0.0
    language: str = ""
    provider: str = ""
    pages: tuple[OCRPageResult, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    @property
    def page_count(self) -> int:
        """Return the number of recognised pages."""
        return len(self.pages)

    @property
    def is_empty(self) -> bool:
        """Return True if no text was recognised."""
        return not self.text.strip()
