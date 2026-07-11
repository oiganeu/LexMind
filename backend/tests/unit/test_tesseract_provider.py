"""Tests for the Tesseract OCR provider (TASK-0024).

Covers:
    - TesseractConfig: validation, config string, language override
    - OCRResultMapper: confidence normalisation, page grouping, filtering
    - TesseractOCRProvider: init, recognize, invalid input, language
      selection, confidence mapping, MIME support, OCRPipeline integration
    - PytesseractEngine: lazy-import adapter against fake modules
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from lexmind.ocr.ocr_provider import OCRProvider
from lexmind.ocr.ocr_result import OCRResult
from lexmind.ocr.providers.ocr_result_mapper import (
    OCRResultMapper,
    TesseractRawOutput,
    TesseractWord,
)
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_provider import (
    PytesseractEngine,
    TesseractEngine,
    TesseractOCRProvider,
)

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeEngine:
    """A fake Tesseract engine capturing invocation arguments."""

    def __init__(self, output: TesseractRawOutput | None = None) -> None:
        self._output = output or TesseractRawOutput(
            text="hello world",
            words=(
                TesseractWord(text="hello", confidence=90.0, page_number=1),
                TesseractWord(text="world", confidence=80.0, page_number=1),
            ),
        )
        self.calls: list[tuple[bytes, TesseractConfig, str]] = []

    def run(
        self,
        image_data: bytes,
        config: TesseractConfig,
        language: str,
    ) -> TesseractRawOutput:
        self.calls.append((image_data, config, language))
        return self._output


# ===========================================================================
# TesseractConfig
# ===========================================================================


class TestTesseractConfig:
    """Test configuration validation and helpers."""

    def test_defaults(self) -> None:
        """Default config uses eng / psm 3 / oem 3."""
        cfg = TesseractConfig()
        assert cfg.language == "eng"
        assert cfg.psm == 3
        assert cfg.oem == 3

    def test_config_string(self) -> None:
        """to_config_string emits psm and oem flags."""
        cfg = TesseractConfig(psm=6, oem=1)
        assert cfg.to_config_string() == "--psm 6 --oem 1"

    def test_config_string_with_extra(self) -> None:
        """Extra config flags are appended."""
        cfg = TesseractConfig(extra_config="-c preserve_interword_spaces=1")
        assert "preserve_interword_spaces=1" in cfg.to_config_string()

    def test_empty_language_rejected(self) -> None:
        """Empty language raises."""
        with pytest.raises(ValueError, match="language"):
            TesseractConfig(language="")

    def test_invalid_psm(self) -> None:
        """Out-of-range psm raises."""
        with pytest.raises(ValueError, match="psm"):
            TesseractConfig(psm=99)

    def test_invalid_oem(self) -> None:
        """Out-of-range oem raises."""
        with pytest.raises(ValueError, match="oem"):
            TesseractConfig(oem=9)

    def test_negative_timeout(self) -> None:
        """Negative timeout raises."""
        with pytest.raises(ValueError, match="timeout"):
            TesseractConfig(timeout=-1.0)

    def test_invalid_min_confidence(self) -> None:
        """Out-of-range min_confidence raises."""
        with pytest.raises(ValueError, match="min_confidence"):
            TesseractConfig(min_confidence=200.0)

    def test_with_language_override(self) -> None:
        """with_language returns a new config with the given language."""
        cfg = TesseractConfig(language="eng")
        updated = cfg.with_language("ron")
        assert updated.language == "ron"
        assert cfg.language == "eng"

    def test_with_language_same_returns_self(self) -> None:
        """with_language returns self when the language is unchanged."""
        cfg = TesseractConfig(language="eng")
        assert cfg.with_language("eng") is cfg
        assert cfg.with_language("") is cfg


# ===========================================================================
# OCRResultMapper
# ===========================================================================


class TestOCRResultMapper:
    """Test raw-output mapping."""

    def test_maps_text_and_provider(self) -> None:
        """Mapper preserves text and sets the provider name."""
        raw = TesseractRawOutput(
            text="abc",
            words=(TesseractWord("abc", 100.0, 1),),
        )
        result = OCRResultMapper().to_result(raw, language="ron")
        assert result.text == "abc"
        assert result.provider == "tesseract"
        assert result.language == "ron"

    def test_confidence_normalised(self) -> None:
        """Confidence is the mean normalised to [0, 1]."""
        raw = TesseractRawOutput(
            words=(
                TesseractWord("a", 90.0, 1),
                TesseractWord("b", 70.0, 1),
            ),
        )
        result = OCRResultMapper().to_result(raw, language="eng")
        assert result.confidence == pytest.approx(0.8)

    def test_page_grouping(self) -> None:
        """Words are grouped into per-page results."""
        raw = TesseractRawOutput(
            text="p1 p2",
            words=(
                TesseractWord("p1", 100.0, 1),
                TesseractWord("p2", 50.0, 2),
            ),
        )
        result = OCRResultMapper().to_result(raw, language="eng")
        assert result.page_count == 2
        assert result.pages[0].page_number == 1
        assert result.pages[0].text == "p1"
        assert result.pages[1].text == "p2"

    def test_filters_negative_confidence(self) -> None:
        """Words with -1 confidence (non-text) are dropped."""
        raw = TesseractRawOutput(
            words=(
                TesseractWord("real", 80.0, 1),
                TesseractWord("noise", -1.0, 1),
            ),
        )
        result = OCRResultMapper().to_result(raw, language="eng")
        assert result.pages[0].text == "real"
        assert result.confidence == pytest.approx(0.8)

    def test_min_confidence_filter(self) -> None:
        """Words below min_confidence are dropped."""
        raw = TesseractRawOutput(
            words=(
                TesseractWord("keep", 90.0, 1),
                TesseractWord("drop", 40.0, 1),
            ),
        )
        result = OCRResultMapper().to_result(
            raw, language="eng", min_confidence=50.0
        )
        assert result.pages[0].text == "keep"

    def test_empty_words(self) -> None:
        """No words yields zero confidence and no pages."""
        raw = TesseractRawOutput(text="")
        result = OCRResultMapper().to_result(raw, language="eng")
        assert result.confidence == 0.0
        assert result.page_count == 0


# ===========================================================================
# TesseractOCRProvider
# ===========================================================================


class TestTesseractOCRProvider:
    """Test the provider behaviour."""

    def test_initialize(self) -> None:
        """Provider initialises with defaults."""
        provider = TesseractOCRProvider()
        assert provider.name == "tesseract"
        assert isinstance(provider.config, TesseractConfig)

    def test_satisfies_ocr_provider_protocol(self) -> None:
        """Provider satisfies the OCRProvider protocol."""
        assert isinstance(TesseractOCRProvider(engine=FakeEngine()), OCRProvider)

    def test_fake_engine_satisfies_engine_protocol(self) -> None:
        """FakeEngine satisfies the TesseractEngine protocol."""
        assert isinstance(FakeEngine(), TesseractEngine)

    def test_recognize_image(self) -> None:
        """Recognize returns a normalized OCRResult."""
        provider = TesseractOCRProvider(engine=FakeEngine())
        result = provider.recognize(b"image-bytes", mime_type="image/png")
        assert isinstance(result, OCRResult)
        assert result.text == "hello world"
        assert result.provider == "tesseract"

    def test_recognize_empty_input_raises(self) -> None:
        """Empty input raises ValueError."""
        provider = TesseractOCRProvider(engine=FakeEngine())
        with pytest.raises(ValueError, match="image_data"):
            provider.recognize(b"")

    def test_language_selection(self) -> None:
        """The requested language overrides the configured default."""
        engine = FakeEngine()
        provider = TesseractOCRProvider(
            config=TesseractConfig(language="eng"), engine=engine
        )
        provider.recognize(b"data", language="ron")
        # engine receives the overridden language
        assert engine.calls[0][2] == "ron"

    def test_language_defaults_to_config(self) -> None:
        """When no language is given, the config default is used."""
        engine = FakeEngine()
        provider = TesseractOCRProvider(
            config=TesseractConfig(language="deu"), engine=engine
        )
        provider.recognize(b"data")
        assert engine.calls[0][2] == "deu"

    def test_confidence_mapping(self) -> None:
        """Confidence is mapped from the engine output."""
        engine = FakeEngine(
            TesseractRawOutput(
                text="x",
                words=(TesseractWord("x", 60.0, 1),),
            )
        )
        provider = TesseractOCRProvider(engine=engine)
        result = provider.recognize(b"data")
        assert result.confidence == pytest.approx(0.6)

    def test_min_confidence_applied(self) -> None:
        """The config min_confidence is passed through to the mapper."""
        engine = FakeEngine(
            TesseractRawOutput(
                text="hi lo",
                words=(
                    TesseractWord("hi", 95.0, 1),
                    TesseractWord("lo", 10.0, 1),
                ),
            )
        )
        provider = TesseractOCRProvider(
            config=TesseractConfig(min_confidence=50.0), engine=engine
        )
        result = provider.recognize(b"data")
        assert result.pages[0].text == "hi"

    def test_supports_mime_types(self) -> None:
        """supports reports the expected MIME types."""
        provider = TesseractOCRProvider(engine=FakeEngine())
        assert provider.supports("image/png")
        assert provider.supports("application/pdf")
        assert provider.supports("IMAGE/PNG")  # case-insensitive
        assert not provider.supports("text/plain")

    def test_repr(self) -> None:
        """__repr__ reports the language."""
        provider = TesseractOCRProvider(
            config=TesseractConfig(language="ron"), engine=FakeEngine()
        )
        assert "ron" in repr(provider)


# ===========================================================================
# OCRPipeline integration
# ===========================================================================


class TestPipelineIntegration:
    """Test the provider inside the OCR pipeline."""

    def test_integrates_with_pipeline(self) -> None:
        """The provider works end-to-end through OCRPipeline."""
        from lexmind.ocr.ocr_artifact_writer import OCRArtifactWriter
        from lexmind.ocr.ocr_dispatcher import OCRDispatcher
        from lexmind.ocr.ocr_pipeline import OCRPipeline, OCRRequest

        storage = MagicMock()
        storage.load.return_value = b"image-bytes"

        dispatcher = OCRDispatcher()
        dispatcher.register(TesseractOCRProvider(engine=FakeEngine()))
        writer = OCRArtifactWriter(storage)
        pipeline = OCRPipeline(dispatcher, writer, storage)

        outcome = pipeline.execute(
            OCRRequest(
                workspace_id="ws-1",
                document_id="doc-1",
                source_uri="storage://ws-1/originals/doc-1/scan.png",
                language="ron",
                mime_type="image/png",
            )
        )
        assert outcome.provider == "tesseract"
        assert outcome.result.text == "hello world"


# ===========================================================================
# PytesseractEngine (lazy-import adapter)
# ===========================================================================


class TestPytesseractEngine:
    """Test the default engine against fake pytesseract/PIL modules."""

    @pytest.fixture()
    def fake_tesseract(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Install fake pytesseract and PIL modules in sys.modules."""
        fake_pt = types.ModuleType("pytesseract")

        def image_to_string(image: object, lang: str, config: str) -> str:
            return "hello world"

        def image_to_data(
            image: object, lang: str, config: str, output_type: object
        ) -> dict[str, list[object]]:
            return {
                "text": ["hello", "", "world"],
                "conf": ["90", "-1", "80"],
                "page_num": [1, 1, 1],
            }

        fake_pt.image_to_string = image_to_string  # type: ignore[attr-defined]
        fake_pt.image_to_data = image_to_data  # type: ignore[attr-defined]
        fake_pt.Output = types.SimpleNamespace(DICT="dict")  # type: ignore[attr-defined]

        fake_pil = types.ModuleType("PIL")
        fake_image_mod = types.ModuleType("PIL.Image")
        fake_image_mod.open = lambda buf: "IMAGE"  # type: ignore[attr-defined]
        fake_pil.Image = fake_image_mod  # type: ignore[attr-defined]

        monkeypatch.setitem(sys.modules, "pytesseract", fake_pt)
        monkeypatch.setitem(sys.modules, "PIL", fake_pil)
        monkeypatch.setitem(sys.modules, "PIL.Image", fake_image_mod)

    def test_run_maps_output(self, fake_tesseract: None) -> None:
        """The engine parses fake pytesseract output into raw words."""
        engine = PytesseractEngine()
        raw = engine.run(b"bytes", TesseractConfig(), "eng")
        assert raw.text == "hello world"
        # empty token filtered out, two words remain
        assert len(raw.words) == 2
        assert raw.words[0].text == "hello"
        assert raw.words[0].confidence == 90.0
        assert raw.words[1].text == "world"

    def test_run_through_provider(self, fake_tesseract: None) -> None:
        """The default engine works via the provider."""
        provider = TesseractOCRProvider()
        result = provider.recognize(b"bytes", language="eng")
        assert result.text == "hello world"
        assert result.confidence == pytest.approx(0.85)

    def test_extract_words_missing_columns(self) -> None:
        """Missing conf/page columns fall back to defaults."""
        words = PytesseractEngine._extract_words({"text": ["solo"]})
        assert len(words) == 1
        assert words[0].confidence == -1.0
        assert words[0].page_number == 1
