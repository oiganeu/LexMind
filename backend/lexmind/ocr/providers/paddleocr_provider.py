"""PaddleOCR provider.

PaddleOCR is an OCR engine with strong multilingual support (including
non-Latin scripts). This module isolates all PaddleOCR-specific concerns
behind the platform-wide :class:`~lexmind.ocr.ocr_provider.OCRProvider`
contract, mirroring the structure of the Tesseract provider.

The actual recognition call is delegated to an injectable
:class:`PaddleOCREngine`; the default engine binds to the ``paddleocr``
library but imports it lazily so the module is importable without the
native dependency installed.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import structlog

from lexmind.ocr.ocr_result import OCRPageResult, OCRResult

logger = structlog.get_logger(__name__)

_SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/bmp",
        "image/webp",
    }
)


@dataclass(frozen=True, slots=True)
class PaddleOCRConfig:
    """Configuration for the PaddleOCR engine.

    Attributes:
        language: PaddleOCR language code (e.g. ``en``, ``ch``, ``fr``,
            ``german``, ``ro``).
        use_angle_cls: Whether to run the angle-classification step.
        det_db_box_thresh: Detection box threshold in [0, 1].
        drop_score: Minimum per-word confidence (0-1) to keep a word.
    """

    language: str = "en"
    use_angle_cls: bool = True
    det_db_box_thresh: float = 0.6
    drop_score: float = 0.5

    def __post_init__(self) -> None:
        if not self.language:
            raise ValueError("language is required")
        if not 0.0 <= self.det_db_box_thresh <= 1.0:
            raise ValueError("det_db_box_thresh must be between 0 and 1")
        if not 0.0 <= self.drop_score <= 1.0:
            raise ValueError("drop_score must be between 0 and 1")

    def to_kwargs(self) -> dict[str, object]:
        """Return the keyword arguments for the paddleocr ``ocr`` call."""
        return {
            "lang": self.language,
            "use_angle_cls": self.use_angle_cls,
            "det_db_box_thresh": self.det_db_box_thresh,
        }

    def with_language(self, language: str) -> PaddleOCRConfig:
        """Return a copy of this config using *language* if provided."""
        if not language or language == self.language:
            return self
        return PaddleOCRConfig(
            language=language,
            use_angle_cls=self.use_angle_cls,
            det_db_box_thresh=self.det_db_box_thresh,
            drop_score=self.drop_score,
        )


@dataclass(frozen=True, slots=True)
class PaddleOCRWord:
    """A single recognised word with its confidence and page."""

    text: str
    confidence: float
    page_number: int = 1


@dataclass(frozen=True, slots=True)
class PaddleOCRRawOutput:
    """Raw output produced by the PaddleOCR engine adapter."""

    text: str = ""
    words: tuple[PaddleOCRWord, ...] = field(default_factory=tuple)


@runtime_checkable
class PaddleOCREngine(Protocol):
    """Adapter that performs the actual PaddleOCR recognition."""

    def run(
        self,
        image_data: bytes,
        config: PaddleOCRConfig,
        language: str,
    ) -> PaddleOCRRawOutput:
        """Recognise *image_data* and return raw PaddleOCR output."""
        ...


class PaddleOCRResultMapper:
    """Converts :class:`PaddleOCRRawOutput` into a normalized OCRResult."""

    _PROVIDER_NAME = "paddleocr"

    def to_result(
        self,
        raw: PaddleOCRRawOutput,
        language: str,
        min_confidence: float = 0.0,
    ) -> OCRResult:
        """Map raw PaddleOCR output to a normalized OCRResult.

        Args:
            raw: The raw engine output.
            language: The language used for recognition.
            min_confidence: Discard words below this confidence (0-1).

        Returns:
            A normalized :class:`OCRResult`.
        """
        valid = [w for w in raw.words if w.confidence >= min_confidence]
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
        self, words: list[PaddleOCRWord]
    ) -> tuple[OCRPageResult, ...]:
        """Group words by page and build per-page results."""
        by_page: dict[int, list[PaddleOCRWord]] = {}
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
    def _mean_confidence(words: list[PaddleOCRWord]) -> float:
        """Return the mean confidence (already normalised to [0, 1])."""
        if not words:
            return 0.0
        return sum(w.confidence for w in words) / len(words)


class PaddleOCRProvider:
    """OCR provider implementing recognition via PaddleOCR."""

    _NAME = "paddleocr"

    def __init__(
        self,
        config: PaddleOCRConfig | None = None,
        engine: PaddleOCREngine | None = None,
        mapper: PaddleOCRResultMapper | None = None,
    ) -> None:
        """Initialise the provider with injected collaborators.

        Args:
            config: PaddleOCR configuration.  Defaults to
                :class:`PaddleOCRConfig` defaults.
            engine: The recognition engine.  Defaults to
                :class:`DefaultPaddleEngine`.
            mapper: Raw-output mapper.  Defaults to
                :class:`PaddleOCRResultMapper`.
        """
        self._config = config or PaddleOCRConfig()
        self._engine = engine or DefaultPaddleEngine()
        self._mapper = mapper or PaddleOCRResultMapper()

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._NAME

    @property
    def config(self) -> PaddleOCRConfig:
        """Return the active configuration."""
        return self._config

    def supports(self, mime_type: str) -> bool:
        """Return True if the MIME type is supported by PaddleOCR."""
        return mime_type.lower() in _SUPPORTED_MIME_TYPES

    def recognize(
        self,
        image_data: bytes,
        language: str = "",
        mime_type: str = "",
    ) -> OCRResult:
        """Run PaddleOCR and return a normalized result.

        Args:
            image_data: Raw image bytes.
            language: Optional language override for this call.
            mime_type: Optional MIME type (advisory).

        Returns:
            A normalized :class:`OCRResult`.

        Raises:
            ValueError: If *image_data* is empty.
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        config = self._config.with_language(language)
        effective_language = config.language

        raw = self._engine.run(image_data, config, effective_language)
        result = self._mapper.to_result(
            raw,
            language=effective_language,
            min_confidence=config.drop_score,
        )
        logger.info(
            "paddleocr_recognize",
            language=effective_language,
            page_count=result.page_count,
            confidence=result.confidence,
        )
        return result

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"PaddleOCRProvider(language={self._config.language!r})"


class DefaultPaddleEngine:
    """Default PaddleOCR engine backed by the ``paddleocr`` library.

    The heavy dependency is imported lazily so the provider module can be
    imported (and unit-tested with a stub engine) without it.
    """

    def run(
        self,
        image_data: bytes,
        config: PaddleOCRConfig,
        language: str,
    ) -> PaddleOCRRawOutput:
        """Recognise *image_data* using the paddleocr library."""
        from paddleocr import PaddleOCR  # type: ignore[import-not-found]

        engine = PaddleOCR(**config.to_kwargs())
        image = io.BytesIO(image_data)
        raw_result = engine.ocr(image, cls=config.use_angle_cls)

        words: list[PaddleOCRWord] = []
        texts: list[str] = []
        for line in raw_result or []:
            for _box, (token, score) in line:
                token = str(token).strip()
                if not token:
                    continue
                texts.append(token)
                words.append(
                    PaddleOCRWord(text=token, confidence=float(score))
                )
        return PaddleOCRRawOutput(text=" ".join(texts), words=tuple(words))
