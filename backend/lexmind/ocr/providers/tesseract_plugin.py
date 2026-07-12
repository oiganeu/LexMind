"""Tesseract OCR plugin.

A ready-to-use plugin that bundles the Tesseract OCR engine
(:class:`TesseractOCRProvider`) and registers it with a shared
:class:`OCRDispatcher` on start.  It extends :class:`OCRProviderPlugin` so
all registration wiring is inherited; only the engine construction is
specific to Tesseract.
"""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.providers.plugin import OCRProviderPlugin
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_provider import (
    TesseractEngine,
    TesseractOCRProvider,
)


class TesseractPlugin(OCRProviderPlugin):
    """Plugin that contributes the Tesseract OCR provider."""

    def __init__(
        self,
        dispatcher: OCRDispatcher,
        config: TesseractConfig | None = None,
        engine: TesseractEngine | None = None,
        plugin_id: str = "tesseract-ocr",
    ) -> None:
        """Initialise the Tesseract plugin.

        Args:
            dispatcher: The shared provider dispatcher.
            config: Tesseract configuration.  Defaults to
                :class:`TesseractConfig` defaults.
            engine: Optional recognition engine override (for testing or a
                custom binding).  Defaults to :class:`PytesseractEngine`.
            plugin_id: Explicit plugin id.
        """
        self._tesseract_config = config or TesseractConfig()
        provider = TesseractOCRProvider(
            config=self._tesseract_config,
            engine=engine,
        )
        super().__init__(dispatcher, provider, plugin_id=plugin_id)

    @property
    def tesseract_config(self) -> TesseractConfig:
        """Return the active Tesseract configuration."""
        return self._tesseract_config
