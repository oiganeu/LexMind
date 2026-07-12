"""Unit tests for the PaddleOCR provider and plugin (Task 34)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.paddle_plugin import PaddleOCRPlugin
from lexmind.ocr.providers.paddleocr_provider import (
    PaddleOCRConfig,
    PaddleOCRProvider,
    PaddleOCRRawOutput,
    PaddleOCRResultMapper,
    PaddleOCRWord,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


@dataclass
class FakePaddleEngine:  # noqa: D101 - test double
    raw: PaddleOCRRawOutput

    def run(self, image_data: bytes, config: PaddleOCRConfig, language: str) -> PaddleOCRRawOutput:
        self.seen_language = language
        return self.raw


def _word(text: str, confidence: float, page_number: int = 1) -> PaddleOCRWord:
    return PaddleOCRWord(text=text, confidence=confidence, page_number=page_number)


def test_paddle_config_defaults_and_validation() -> None:
    cfg = PaddleOCRConfig()
    assert cfg.language == "en"
    assert cfg.use_angle_cls is True
    assert cfg.to_kwargs()["lang"] == "en"


    with pytest.raises(ValueError):
        PaddleOCRConfig(language="")
    with pytest.raises(ValueError):
        PaddleOCRConfig(det_db_box_thresh=2.0)
    with pytest.raises(ValueError):
        PaddleOCRConfig(drop_score=-0.1)


def test_paddle_config_with_language() -> None:
    cfg = PaddleOCRConfig(language="en")
    assert cfg.with_language("").language == "en"
    assert cfg.with_language("ro").language == "ro"


def test_mapper_filters_and_normalises() -> None:
    raw = PaddleOCRRawOutput(
        text="hello world drop",
        words=(
            _word("hello", 0.9, page_number=1),
            _word("world", 0.6, page_number=1),
            _word("drop", 0.1, page_number=2),
        ),
    )
    result = PaddleOCRResultMapper().to_result(raw, language="en", min_confidence=0.05)
    assert isinstance(result, OCRResult)
    assert result.provider == "paddleocr"
    assert result.confidence == pytest.approx((0.9 + 0.6 + 0.1) / 3)
    assert result.page_count == 2
    pages = {p.page_number: p for p in result.pages}
    assert pages[1].text == "hello world"
    assert pages[2].text == "drop"


def test_mapper_drops_low_confidence_words() -> None:
    raw = PaddleOCRRawOutput(
        text="keep drop",
        words=(
            _word("keep", 0.9, page_number=1),
            _word("drop", 0.1, page_number=1),
        ),
    )
    result = PaddleOCRResultMapper().to_result(raw, language="en", min_confidence=0.5)
    assert result.confidence == pytest.approx(0.9)
    assert result.pages[0].text == "keep"


def test_provider_recognize_ok() -> None:
    engine = FakePaddleEngine(
        raw=PaddleOCRRawOutput(text="text", words=(_word("text", 0.95),))
    )
    provider = PaddleOCRProvider(engine=engine)
    assert provider.name == "paddleocr"
    assert provider.supports("image/png")
    assert not provider.supports("application/pdf")

    result = provider.recognize(b"data", language="ro")
    assert isinstance(result, OCRResult)
    assert result.text == "text"
    assert result.language == "ro"
    assert engine.seen_language == "ro"


def test_provider_empty_image_raises() -> None:
    provider = PaddleOCRProvider(
        engine=FakePaddleEngine(PaddleOCRRawOutput())
    )

    with pytest.raises(ValueError):
        provider.recognize(b"")


def test_paddle_plugin_is_provider_plugin() -> None:
    plugin = PaddleOCRPlugin(OCRDispatcher())
    assert plugin.provider.name == "paddleocr"
    assert PluginCapability.OCR in plugin.get_metadata().capabilities
    assert plugin.get_metadata().id == "paddleocr"
    assert isinstance(plugin.paddle_config, PaddleOCRConfig)


def test_paddle_plugin_registers_and_recognizes() -> None:
    dispatcher = OCRDispatcher()
    plugin = PaddleOCRPlugin(
        dispatcher,
        engine=FakePaddleEngine(PaddleOCRRawOutput(text="x", words=(_word("x", 0.8),))),
    )
    plugin.start()
    assert plugin.state == PluginState.STARTED
    assert dispatcher.has_provider("paddleocr")
    result = dispatcher.select(name="paddleocr").recognize(b"img")
    assert isinstance(result, OCRResult)
    plugin.stop()
    assert not dispatcher.has_provider("paddleocr")


def test_paddle_plugin_rejects_bad_dispatcher() -> None:

    with pytest.raises(ValueError):
        PaddleOCRPlugin(None)  # type: ignore[arg-type]
