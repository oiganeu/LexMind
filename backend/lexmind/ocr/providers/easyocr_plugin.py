"""EasyOCR plugin.

Ready-to-use packaging of the EasyOCR engine as a LexMind plugin.  It builds
an :class:`EasyOCRProvider` and registers it with a shared
:class:`OCRDispatcher` on start, declaring :class:`PluginCapability.OCR`.
"""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.providers.easyocr_provider import (
    EasyOCRConfig,
    EasyOCREngine,
    EasyOCRProvider,
)
from lexmind.ocr.providers.plugin import OCRProviderPlugin


class EasyOCRPlugin(OCRProviderPlugin):
    """Plugin that contributes the EasyOCR provider."""

    def __init__(
        self,
        dispatcher: OCRDispatcher,
        config: EasyOCRConfig | None = None,
        engine: EasyOCREngine | None = None,
        plugin_id: str = "easyocr",
    ) -> None:
        """Initialise the EasyOCR plugin.

        Args:
            dispatcher: The shared provider dispatcher.
            config: EasyOCR configuration.  Defaults to
                :class:`EasyOCRConfig` defaults.
            engine: Optional recognition engine override.  Defaults to the
                ``easyocr``-backed engine.
            plugin_id: Explicit plugin id.
        """
        self._easy_config = config or EasyOCRConfig()
        provider = EasyOCRProvider(
            config=self._easy_config,
            engine=engine,
        )
        super().__init__(dispatcher, provider, plugin_id=plugin_id)

    @property
    def easy_config(self) -> EasyOCRConfig:
        """Return the active EasyOCR configuration."""
        return self._easy_config
