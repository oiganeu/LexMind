"""Mapping from raw Tesseract output to a normalized OCRResult.

The mapper is the only place that understands the shape of Tesseract's
per-word data.  It converts that into the engine-agnostic
:class:`OCRResult` consumed by the rest of the platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmind.ocr.ocr_result import OCRPageResult, OCRResult

_TESSERACT_CONF_MAX = 100.0


@dataclass(frozen=True, slots=True)
class TesseractWord:
    """A single recognised word with its confidence and page."""

    text: str
    confidence: float
    page_number: int = 1


@dataclass(frozen=True, slots=True)
class TesseractRawOutput:
    """Raw output produced by the Tesseract engine adapter."""

    text: str = ""
    words: tuple[TesseractWord, ...] = field(default_factory=tuple)


class OCRResultMapper:
    """Converts :class:`TesseractRawOutput` into :class:`OCRResult`."""

    _PROVIDER_NAME = "tesseract"

    def to_result(
        self,
        raw: TesseractRawOutput,
        language: str,
        min_confidence: float = 0.0,
    ) -> OCRResult:
        """Map raw Tesseract output to a normalized OCRResult.

        Args:
            raw: The raw engine output.
            language: The language used for recognition.
            min_confidence: Discard words below this confidence (0-100).

        Returns:
            A normalized :class:`OCRResult`.
        """
        valid = [
            w
            for w in raw.words
            if w.confidence >= 0 and w.confidence >= min_confidence
        ]
        overall = self._mean_confidence(valid)
        pages = self._build_pages(valid)
        return OCRResult(
            text=raw.text,
            confidence=overall,
            language=language,
            provider=self._PROVIDER_NAME,
            pages=pages,
        )

    def _build_pages(
        self, words: list[TesseractWord]
    ) -> tuple[OCRPageResult, ...]:
        """Group words by page and build per-page results."""
        by_page: dict[int, list[TesseractWord]] = {}
        for word in words:
            by_page.setdefault(word.page_number, []).append(word)

        pages: list[OCRPageResult] = []
        for page_number in sorted(by_page):
            page_words = by_page[page_number]
            pages.append(
                OCRPageResult(
                    page_number=page_number,
                    text=" ".join(w.text for w in page_words),
                    confidence=self._mean_confidence(page_words),
                )
            )
        return tuple(pages)

    @staticmethod
    def _mean_confidence(words: list[TesseractWord]) -> float:
        """Return the mean confidence normalised to the range [0, 1]."""
        if not words:
            return 0.0
        total = sum(w.confidence for w in words)
        return total / len(words) / _TESSERACT_CONF_MAX
