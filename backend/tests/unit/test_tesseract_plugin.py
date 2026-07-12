"""Unit tests for the Tesseract plugin (Task 33)."""

from __future__ import annotations

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.plugin import OCRProviderPlugin
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_plugin import TesseractPlugin
from lexmind.ocr.providers.tesseract_provider import TesseractRawOutput
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


class FakeTesseractEngine:
    """Fake Tesseract engine for tests."""

    def run(self, image_data: bytes, config: TesseractConfig, language: str) -> TesseractRawOutput:
        return TesseractRawOutput(text="page", words=())


def test_tesseract_plugin_is_provider_plugin() -> None:
    plugin = TesseractPlugin(OCRDispatcher())
    assert isinstance(plugin, OCRProviderPlugin)
    assert plugin.provider.name == "tesseract"
    assert PluginCapability.OCR in plugin.get_metadata().capabilities
    assert plugin.get_metadata().id == "tesseract-ocr"
    assert isinstance(plugin.tesseract_config, TesseractConfig)


def test_tesseract_plugin_registers_and_recognizes() -> None:
    dispatcher = OCRDispatcher()
    plugin = TesseractPlugin(dispatcher, engine=FakeTesseractEngine())
    plugin.start()
    assert plugin.state == PluginState.STARTED
    assert dispatcher.has_provider("tesseract")
    provider = dispatcher.select(name="tesseract")
    result = provider.recognize(b"data")
    assert isinstance(result, OCRResult)
    assert result.provider == "tesseract"
    plugin.stop()
    assert not dispatcher.has_provider("tesseract")


def test_tesseract_plugin_custom_config() -> None:
    cfg = TesseractConfig(language="ron", psm=6)
    plugin = TesseractPlugin(OCRDispatcher(), config=cfg, engine=FakeTesseractEngine())
    assert plugin.tesseract_config.language == "ron"
    assert plugin.tesseract_config.psm == 6


def test_tesseract_plugin_supports_expected_mimes() -> None:
    plugin = TesseractPlugin(OCRDispatcher(), engine=FakeTesseractEngine())
    assert plugin.provider.supports("image/png")
    assert plugin.provider.supports("application/pdf")
    assert not plugin.provider.supports("text/plain")


def test_tesseract_plugin_rejects_bad_dispatcher() -> None:
    import pytest

    with pytest.raises(ValueError):
        TesseractPlugin(None)  # type: ignore[arg-type]
