"""PaddleOCR plugin.

Ready-to-use packaging of the PaddleOCR engine as a LexMind plugin.  It
builds a :class:`PaddleOCRProvider` and registers it with a shared
:class:`OCRDispatcher` on start, declaring :class:`PluginCapability.OCR`.
"""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.providers.paddleocr_provider import (
    PaddleOCRConfig,
    PaddleOCREngine,
    PaddleOCRProvider,
)
from lexmind.ocr.providers.plugin import OCRProviderPlugin


class PaddleOCRPlugin(OCRProviderPlugin):
    """Plugin that contributes the PaddleOCR provider."""

    def __init__(
        self,
        dispatcher: OCRDispatcher,
        config: PaddleOCRConfig | None = None,
        engine: PaddleOCREngine | None = None,
        plugin_id: str = "paddleocr",
    ) -> None:
        """Initialise the PaddleOCR plugin.

        Args:
            dispatcher: The shared provider dispatcher.
            config: PaddleOCR configuration.  Defaults to
                :class:`PaddleOCRConfig` defaults.
            engine: Optional recognition engine override.  Defaults to the
                ``paddleocr``-backed engine.
            plugin_id: Explicit plugin id.
        """
        self._paddle_config = config or PaddleOCRConfig()
        provider = PaddleOCRProvider(
            config=self._paddle_config,
            engine=engine,
        )
        super().__init__(dispatcher, provider, plugin_id=plugin_id)

    @property
    def paddle_config(self) -> PaddleOCRConfig:
        """Return the active PaddleOCR configuration."""
        return self._paddle_config
