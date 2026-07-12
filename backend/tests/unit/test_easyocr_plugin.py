"""Unit tests for the EasyOCR provider and plugin (Task 35)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.easyocr_plugin import EasyOCRPlugin
from lexmind.ocr.providers.easyocr_provider import (
    EasyOCRConfig,
    EasyOCRProvider,
    EasyOCRRawOutput,
    EasyOCRResultMapper,
    EasyOCRWord,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


@dataclass
class FakeEasyEngine:  # noqa: D101 - test double
    raw: EasyOCRRawOutput

    def run(
        self, image_data: bytes, config: EasyOCRConfig, languages: tuple[str, ...]
    ) -> EasyOCRRawOutput:
        self.seen_languages = languages
        return self.raw


def _word(text: str, confidence: float, page_number: int = 1) -> EasyOCRWord:
    return EasyOCRWord(text=text, confidence=confidence, page_number=page_number)


def test_easy_config_defaults_and_validation() -> None:
    cfg = EasyOCRConfig()
    assert cfg.languages == ("en",)
    assert cfg.to_kwargs()["lang_list"] == ["en"]

    with pytest.raises(ValueError):
        EasyOCRConfig(languages=())
    with pytest.raises(ValueError):
        EasyOCRConfig(detail=2)
    with pytest.raises(ValueError):
        EasyOCRConfig(min_confidence=2.0)


def test_easy_config_with_languages() -> None:
    cfg = EasyOCRConfig(languages=("en",))
    assert cfg.with_languages(()).languages == ("en",)
    assert cfg.with_languages(("ro", "en")).languages == ("ro", "en")


def test_mapper_filters_and_normalises() -> None:
    raw = EasyOCRRawOutput(
        text="hello world drop",
        words=(
            _word("hello", 0.9, page_number=1),
            _word("world", 0.6, page_number=1),
            _word("drop", 0.1, page_number=2),
        ),
    )
    result = EasyOCRResultMapper().to_result(
        raw, languages=("en",), min_confidence=0.05
    )
    assert isinstance(result, OCRResult)
    assert result.provider == "easyocr"
    assert result.language == "en"
    assert result.confidence == pytest.approx((0.9 + 0.6 + 0.1) / 3)
    assert result.page_count == 2
    pages = {p.page_number: p for p in result.pages}
    assert pages[1].text == "hello world"
    assert pages[2].text == "drop"


def test_provider_recognize_ok() -> None:
    engine = FakeEasyEngine(
        raw=EasyOCRRawOutput(text="text", words=(_word("text", 0.95),))
    )
    provider = EasyOCRProvider(engine=engine)
    assert provider.name == "easyocr"
    assert provider.supports("image/png")
    assert provider.supports("image/tiff")
    assert not provider.supports("application/pdf")

    result = provider.recognize(b"data", language="ro")
    assert isinstance(result, OCRResult)
    assert result.text == "text"
    assert result.language == "ro"
    assert engine.seen_languages == ("ro",)


def test_provider_empty_image_raises() -> None:
    provider = EasyOCRProvider(engine=FakeEasyEngine(EasyOCRRawOutput()))
    with pytest.raises(ValueError):
        provider.recognize(b"")


def test_easy_plugin_is_provider_plugin() -> None:
    plugin = EasyOCRPlugin(OCRDispatcher())
    assert plugin.provider.name == "easyocr"
    assert PluginCapability.OCR in plugin.get_metadata().capabilities
    assert plugin.get_metadata().id == "easyocr"
    assert isinstance(plugin.easy_config, EasyOCRConfig)


def test_easy_plugin_registers_and_recognizes() -> None:
    dispatcher = OCRDispatcher()
    plugin = EasyOCRPlugin(
        dispatcher,
        engine=FakeEasyEngine(EasyOCRRawOutput(text="x", words=(_word("x", 0.8),))),
    )
    plugin.start()
    assert plugin.state == PluginState.STARTED
    assert dispatcher.has_provider("easyocr")
    result = dispatcher.select(name="easyocr").recognize(b"img")
    assert isinstance(result, OCRResult)
    plugin.stop()
    assert not dispatcher.has_provider("easyocr")


def test_easy_plugin_rejects_bad_dispatcher() -> None:
    with pytest.raises(ValueError):
        EasyOCRPlugin(None)  # type: ignore[arg-type]
