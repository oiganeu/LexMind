"""Unit tests for the OCR provider plugin (Task 32)."""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher, OCRProviderNotFoundError
from lexmind.ocr.ocr_provider import OCRProvider
from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.plugin import OCRProviderPlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


class StubProvider:
    """Minimal OCRProvider implementation for tests."""

    name = "stub"
    _supports = ("image/png",)

    def supports(self, mime_type: str) -> bool:  # noqa: D401 - test double
        return mime_type in self._supports

    def recognize(self, image_data: bytes, language: str = "", mime_type: str = "") -> OCRResult:
        return OCRResult(text="x", provider=self.name)


def test_plugin_declares_ocr_capability() -> None:
    dispatcher = OCRDispatcher()
    plugin = OCRProviderPlugin(dispatcher, StubProvider())
    assert PluginCapability.OCR in plugin.get_metadata().capabilities
    assert plugin.provider.name == "stub"
    assert plugin.dispatcher is dispatcher


def test_plugin_registers_on_start() -> None:
    dispatcher = OCRDispatcher()
    plugin = OCRProviderPlugin(dispatcher, StubProvider())
    plugin.start()
    assert dispatcher.has_provider("stub")
    assert dispatcher.default_provider == "stub"
    assert plugin.state == PluginState.STARTED


def test_plugin_unregisters_on_stop() -> None:
    dispatcher = OCRDispatcher()
    plugin = OCRProviderPlugin(dispatcher, StubProvider())
    plugin.start()
    plugin.stop()
    assert not dispatcher.has_provider("stub")
    assert dispatcher.default_provider is None


def test_plugin_explicit_id() -> None:
    plugin = OCRProviderPlugin(OCRDispatcher(), StubProvider(), plugin_id="my-ocr")
    assert plugin.get_metadata().id == "my-ocr"


def test_plugin_rejects_bad_args() -> None:
    import pytest

    with pytest.raises(ValueError):
        OCRProviderPlugin(None, StubProvider())  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        OCRProviderPlugin(OCRDispatcher(), None)  # type: ignore[arg-type]


def test_plugin_provider_is_selectable() -> None:
    dispatcher = OCRDispatcher()
    plugin = OCRProviderPlugin(dispatcher, StubProvider())
    plugin.start()
    provider = dispatcher.select(mime_type="image/png")
    assert isinstance(provider, OCRProvider)
    assert provider.name == "stub"
    provider = dispatcher.select(name="stub")
    assert provider.name == "stub"
    import pytest

    with pytest.raises(OCRProviderNotFoundError):
        dispatcher.select(mime_type="text/plain")
