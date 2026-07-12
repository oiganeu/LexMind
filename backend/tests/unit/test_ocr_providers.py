"""Unit tests for the OCR provider layer (Tesseract engine, config, mapper)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.ocr_result_mapper import (
    OCRResultMapper,
    TesseractRawOutput,
    TesseractWord,
)
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_provider import (
    TesseractOCRProvider,
)


@dataclass
class FakeTesseractEngine:  # noqa: D101 - test double
    raw: TesseractRawOutput

    def run(
        self,
        image_data: bytes,
        config: TesseractConfig,
        language: str,
    ) -> TesseractRawOutput:
        self.seen_language = language
        self.seen_config = config
        return self.raw


def _word(text: str, confidence: float, page_number: int = 1) -> TesseractWord:
    return TesseractWord(text=text, confidence=confidence, page_number=page_number)


def test_tesseract_config_defaults_valid() -> None:
    cfg = TesseractConfig()
    assert cfg.language == "eng"
    assert cfg.psm == 3
    assert cfg.oem == 3
    assert cfg.to_config_string() == "--psm 3 --oem 3"


def test_tesseract_config_validation() -> None:
    with pytest.raises(ValueError):
        TesseractConfig(language="")
    with pytest.raises(ValueError):
        TesseractConfig(psm=99)
    with pytest.raises(ValueError):
        TesseractConfig(oem=9)
    with pytest.raises(ValueError):
        TesseractConfig(timeout=-1.0)
    with pytest.raises(ValueError):
        TesseractConfig(min_confidence=101.0)


def test_tesseract_config_with_language() -> None:
    cfg = TesseractConfig(language="eng")
    same = cfg.with_language("")
    assert same is cfg
    changed = cfg.with_language("ron")
    assert changed.language == "ron"
    assert changed.psm == cfg.psm


def test_mapper_empty_words() -> None:
    result = OCRResultMapper().to_result(
        TesseractRawOutput(text=""), language="ron"
    )
    assert isinstance(result, OCRResult)
    assert result.text == ""
    assert result.confidence == 0.0
    assert result.provider == "tesseract"
    assert result.page_count == 0


def test_mapper_builds_pages_and_confidence() -> None:
    raw = TesseractRawOutput(
        text="hello world",
        words=(
            _word("hello", 80.0, page_number=1),
            _word("world", 60.0, page_number=1),
            _word("foo", 40.0, page_number=2),
        ),
    )
    result = OCRResultMapper().to_result(raw, language="eng")
    assert result.confidence == pytest.approx((80.0 + 60.0 + 40.0) / 3 / 100.0)
    assert result.page_count == 2
    pages = {p.page_number: p for p in result.pages}
    assert pages[1].text == "hello world"
    assert pages[2].text == "foo"


def test_mapper_filters_low_confidence() -> None:
    raw = TesseractRawOutput(
        text="keep drop",
        words=(
            _word("keep", 90.0, page_number=1),
            _word("drop", 10.0, page_number=1),
        ),
    )
    result = OCRResultMapper().to_result(raw, language="eng", min_confidence=50.0)
    assert result.confidence == pytest.approx(90.0 / 100.0)
    assert result.pages[0].text == "keep"


def test_provider_name_and_supports() -> None:
    provider = TesseractOCRProvider()
    assert provider.name == "tesseract"
    assert provider.supports("image/png")
    assert provider.supports("application/pdf")
    assert not provider.supports("text/plain")


def test_provider_recognize_ok() -> None:
    engine = FakeTesseractEngine(
        raw=TesseractRawOutput(text="rechn", words=(_word("rechn", 90.0),))
    )
    provider = TesseractOCRProvider(engine=engine)
    result = provider.recognize(b"data", language="ron")
    assert isinstance(result, OCRResult)
    assert result.text == "rechn"
    assert result.provider == "tesseract"
    assert result.language == "ron"
    assert engine.seen_language == "ron"


def test_provider_recognize_empty_image_raises() -> None:
    provider = TesseractOCRProvider(engine=FakeTesseractEngine(TesseractRawOutput()))
    with pytest.raises(ValueError):
        provider.recognize(b"")


def test_provider_uses_configured_language() -> None:
    engine = FakeTesseractEngine(TesseractRawOutput(text="x", words=(_word("x", 70.0),)))
    provider = TesseractOCRProvider(
        config=TesseractConfig(language="fra"), engine=engine
    )
    provider.recognize(b"data", language="")
    assert engine.seen_language == "fra"


def test_provider_exposes_config_and_repr() -> None:
    cfg = TesseractConfig(language="ron")
    provider = TesseractOCRProvider(config=cfg, engine=FakeTesseractEngine(TesseractRawOutput()))
    assert provider.config is cfg
    assert "ron" in repr(provider)
