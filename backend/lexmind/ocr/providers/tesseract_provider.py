"""Tesseract OCR provider.

Wraps the Tesseract engine behind the platform-wide
:class:`~lexmind.ocr.ocr_provider.OCRProvider` contract.  All
Tesseract-specific access is confined to this module; the actual engine
call is delegated to an injectable :class:`TesseractEngine`, which keeps
the provider testable without the native binary installed.
"""

from __future__ import annotations

import io
from typing import Protocol, runtime_checkable

import structlog

from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.ocr_result_mapper import (
    OCRResultMapper,
    TesseractRawOutput,
    TesseractWord,
)
from lexmind.ocr.providers.tesseract_config import TesseractConfig

logger = structlog.get_logger(__name__)

_SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/tiff",
        "image/bmp",
        "application/pdf",
    }
)


@runtime_checkable
class TesseractEngine(Protocol):
    """Adapter that performs the actual Tesseract recognition."""

    def run(
        self,
        image_data: bytes,
        config: TesseractConfig,
        language: str,
    ) -> TesseractRawOutput:
        """Recognise *image_data* and return raw Tesseract output."""
        ...


class PytesseractEngine:
    """Default engine backed by ``pytesseract`` and ``Pillow``.

    The heavy dependencies are imported lazily so the module can be
    imported (and the rest of the provider tested) without them.
    """

    def run(
        self,
        image_data: bytes,
        config: TesseractConfig,
        language: str,
    ) -> TesseractRawOutput:
        """Recognise *image_data* using pytesseract."""
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_data))
        config_string = config.to_config_string()
        text = pytesseract.image_to_string(
            image, lang=language, config=config_string
        )
        data = pytesseract.image_to_data(
            image,
            lang=language,
            config=config_string,
            output_type=pytesseract.Output.DICT,
        )
        return TesseractRawOutput(
            text=text,
            words=self._extract_words(data),
        )

    @staticmethod
    def _extract_words(data: dict[str, list[object]]) -> tuple[TesseractWord, ...]:
        """Extract non-empty words from pytesseract's TSV-style dict."""
        texts = data.get("text", [])
        confs = data.get("conf", [])
        pages = data.get("page_num", [])
        words: list[TesseractWord] = []
        for index, raw_text in enumerate(texts):
            token = str(raw_text).strip()
            if not token:
                continue
            confidence = float(confs[index]) if index < len(confs) else -1.0
            page = int(pages[index]) if index < len(pages) else 1
            words.append(
                TesseractWord(
                    text=token,
                    confidence=confidence,
                    page_number=page,
                )
            )
        return tuple(words)


class TesseractOCRProvider:
    """OCR provider implementing recognition via Tesseract."""

    _NAME = "tesseract"

    def __init__(
        self,
        config: TesseractConfig | None = None,
        engine: TesseractEngine | None = None,
        mapper: OCRResultMapper | None = None,
    ) -> None:
        """Initialise the provider with injected collaborators.

        Args:
            config: Tesseract configuration.  Defaults to
                :class:`TesseractConfig` defaults.
            engine: The recognition engine.  Defaults to
                :class:`PytesseractEngine`.
            mapper: Raw-output mapper.  Defaults to
                :class:`OCRResultMapper`.
        """
        self._config = config or TesseractConfig()
        self._engine = engine or PytesseractEngine()
        self._mapper = mapper or OCRResultMapper()

    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._NAME

    @property
    def config(self) -> TesseractConfig:
        """Return the active configuration."""
        return self._config

    def supports(self, mime_type: str) -> bool:
        """Return True if the MIME type is supported by Tesseract."""
        return mime_type.lower() in _SUPPORTED_MIME_TYPES

    def recognize(
        self,
        image_data: bytes,
        language: str = "",
        mime_type: str = "",
    ) -> OCRResult:
        """Run Tesseract OCR and return a normalized result.

        Args:
            image_data: Raw image or PDF bytes.
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
            min_confidence=config.min_confidence,
        )
        logger.info(
            "tesseract_recognize",
            language=effective_language,
            page_count=result.page_count,
            confidence=result.confidence,
        )
        return result

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"TesseractOCRProvider(language={self._config.language!r})"
