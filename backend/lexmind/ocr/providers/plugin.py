"""OCR provider plugin.

Bridges the OCR provider interface into the plugin framework.  An
:class:`OCRProviderPlugin` wraps a concrete :class:`OCRProvider` and, on
start, registers it with the shared :class:`OCRDispatcher` so the OCR
pipeline can discover and use it.  On stop it unregisters the provider,
keeping the dispatcher consistent without any global state.
"""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.ocr_provider import OCRProvider
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OCRProviderPlugin(BasePlugin):
    """Plugin that contributes an OCR provider to the dispatcher."""

    def __init__(
        self,
        dispatcher: OCRDispatcher,
        provider: OCRProvider,
        plugin_id: str | None = None,
    ) -> None:
        """Initialise the plugin.

        Args:
            dispatcher: The shared provider registry/dispatcher.
            provider: The OCR provider this plugin contributes.
            plugin_id: Optional explicit plugin id; defaults to
                ``ocr-<provider.name>``.
        """
        if dispatcher is None:
            raise ValueError("dispatcher must not be None")
        if provider is None:
            raise ValueError("provider must not be None")
        super().__init__(
            id=plugin_id or f"ocr-{provider.name}",
            name=f"OCR Provider: {provider.name}",
            version="1.0.0",
            description=f"OCR provider plugin backed by {provider.name}.",
            capabilities=(PluginCapability.OCR,),
        )
        self._dispatcher = dispatcher
        self._provider = provider

    @property
    def provider(self) -> OCRProvider:
        """Return the wrapped OCR provider."""
        return self._provider

    @property
    def dispatcher(self) -> OCRDispatcher:
        """Return the shared dispatcher this plugin registers into."""
        return self._dispatcher

    def start(self) -> None:
        """Register the provider with the dispatcher."""
        self._dispatcher.register(self._provider)
        super().start()

    def stop(self) -> None:
        """Unregister the provider from the dispatcher."""
        self._dispatcher.unregister(self._provider.name)
        super().stop()
