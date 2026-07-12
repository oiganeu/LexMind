"""EasyOCR provider.

EasyOCR is a ready-to-use OCR engine supporting 80+ languages. This module
isolates all EasyOCR-specific concerns behind the platform-wide
:class:`~lexmind.ocr.ocr_provider.OCRProvider` contract, mirroring the
structure of the Tesseract and PaddleOCR providers.

The actual recognition call is delegated to an injectable
:class:`EasyOCREngine`; the default engine binds to the ``easyocr`` library
but imports it lazily so the module is importable without the native
dependency installed.
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
        "image/tiff",
    }
)


@dataclass(frozen=True, slots=True)
class EasyOCRConfig:
    """Configuration for the EasyOCR engine.

    Attributes:
        languages: Language codes EasyOCR should load (e.g. ``("en",)``,
            ``("ro", "en")``).
        gpu: Whether to use a GPU for recognition.
        detail: ``readtext`` detail level (1 = include boxes, 0 = text only).
        min_confidence: Minimum per-word confidence (0-1) to keep a word.
    """

    languages: tuple[str, ...] = ("en",)
    gpu: bool = False
    detail: int = 1
    min_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.languages:
            raise ValueError("at least one language is required")
        if self.detail not in (0, 1):
            raise ValueError("detail must be 0 or 1")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def to_kwargs(self) -> dict[str, object]:
        """Return the keyword arguments for the ``easyocr.Reader`` call."""
        return {"lang_list": list(self.languages), "gpu": self.gpu}

    def with_languages(self, languages: tuple[str, ...]) -> EasyOCRConfig:
        """Return a copy of this config using *languages* if provided."""
        if not languages or languages == self.languages:
            return self
        return EasyOCRConfig(
            languages=languages,
            gpu=self.gpu,
            detail=self.detail,
            min_confidence=self.min_confidence,
        )


@dataclass(frozen=True, slots=True)
class EasyOCRWord:
    """A single recognised word with its confidence and page."""

    text: str
    confidence: float
    page_number: int = 1


@dataclass(frozen=True, slots=True)
class EasyOCRRawOutput:
    """Raw output produced by the EasyOCR engine adapter."""

    text: str = ""
    words: tuple[EasyOCRWord, ...] = field(default_factory=tuple)


@runtime_checkable
class EasyOCREngine(Protocol):
    """Adapter that performs the actual EasyOCR recognition."""

    def run(
        self,
        image_data: bytes,
        config: EasyOCRConfig,
        languages: tuple[str, ...],
    ) -> EasyOCRRawOutput:
        """Recognise *image_data* and return raw EasyOCR output."""
        ...


class EasyOCRResultMapper:
    """Converts :class:`EasyOCRRawOutput` into a normalized OCRResult."""

    _PROVIDER_NAME = "easyocr"

    def to_result(
        self,
        raw: EasyOCRRawOutput,
        languages: tuple[str, ...],
        min_confidence: float = 0.0,
    ) -> OCRResult:
        """Map raw EasyOCR output to a normalized OCRResult.

        Args:
            raw: The raw engine output.
            languages: The languages used for recognition.
            min_confidence: Discard words below this confidence (0-1).

        Returns:
            A normalized :class:`OCRResult`.
        """
        language = languages[0] if languages else ""
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
        self, words: list[EasyOCRWord]
    ) -> tuple[OCRPageResult, ...]:
        """Group words by page and build per-page results."""
        by_page: dict[int, list[EasyOCRWord]] = {}
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
    def _mean_confidence(words: list[EasyOCRWord]) -> float:
        """Return the mean confidence (already normalised to [0, 1])."""
        if not words:
            return 0.0
        return sum(w.confidence for w in words) / len(words)


class EasyOCRProvider:
    """OCR provider implementing recognition via EasyOCR."""

    _NAME = "easyocr"

    def __init__(
        self,
        config: EasyOCRConfig | None = None,
        engine: EasyOCREngine | None = None,
        mapper: EasyOCRResultMapper | None = None,
    ) -> None:
        """Initialise the provider with injected collaborators.

        Args:
            config: EasyOCR configuration.  Defaults to
                :class:`EasyOCRConfig` defaults.
            engine: The recognition engine.  Defaults to
                :class:`DefaultEasyEngine`.
            mapper: Raw-output mapper.  Defaults to
                :class:`EasyOCRResultMapper`.
        """
        self._config = config or EasyOCRConfig()
        self._engine = engine or DefaultEasyEngine()
        self._mapper = mapper or EasyOCRResultMapper()

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._NAME

    @property
    def config(self) -> EasyOCRConfig:
        """Return the active configuration."""
        return self._config

    def supports(self, mime_type: str) -> bool:
        """Return True if the MIME type is supported by EasyOCR."""
        return mime_type.lower() in _SUPPORTED_MIME_TYPES

    def recognize(
        self,
        image_data: bytes,
        language: str = "",
        mime_type: str = "",
    ) -> OCRResult:
        """Run EasyOCR and return a normalized result.

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

        config = self._config.with_languages(
            (language,) if language else self._config.languages
        )
        raw = self._engine.run(image_data, config, config.languages)
        result = self._mapper.to_result(
            raw,
            languages=config.languages,
            min_confidence=config.min_confidence,
        )
        logger.info(
            "easyocr_recognize",
            languages=config.languages,
            page_count=result.page_count,
            confidence=result.confidence,
        )
        return result

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"EasyOCRProvider(languages={self._config.languages!r})"


class DefaultEasyEngine:
    """Default EasyOCR engine backed by the ``easyocr`` library.

    The heavy dependency is imported lazily so the provider module can be
    imported (and unit-tested with a stub engine) without it.
    """

    def run(
        self,
        image_data: bytes,
        config: EasyOCRConfig,
        languages: tuple[str, ...],
    ) -> EasyOCRRawOutput:
        """Recognise *image_data* using the easyocr library."""
        import easyocr  # type: ignore[import-not-found]

        reader = easyocr.Reader(**config.to_kwargs())
        image = io.BytesIO(image_data)
        raw_result = reader.readtext(image.read(), detail=config.detail)

        words: list[EasyOCRWord] = []
        texts: list[str] = []
        for entry in raw_result or []:
            if len(entry) < 3:
                continue
            _box, token, score = entry[0], entry[1], entry[2]
            token = str(token).strip()
            if not token:
                continue
            texts.append(token)
            words.append(EasyOCRWord(text=token, confidence=float(score)))
        return EasyOCRRawOutput(text=" ".join(texts), words=tuple(words))
