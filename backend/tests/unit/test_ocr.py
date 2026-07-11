"""Tests for the OCR orchestration layer (TASK-0023).

Covers:
    - OCRResult / OCRPageResult: construction and validation
    - OCRDispatcher: register, select, default, mime fallback, errors
    - OCRArtifactWriter: text + JSON persistence via StorageManager
    - OCRPipeline: successful flow, failure flow, event publication
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from lexmind.ocr.ocr_artifact_writer import OCRArtifactWriter
from lexmind.ocr.ocr_dispatcher import OCRDispatcher, OCRProviderNotFoundError
from lexmind.ocr.ocr_events import OCRCompleted, OCRFailed, OCRStarted
from lexmind.ocr.ocr_pipeline import OCROutcome, OCRPipeline, OCRRequest
from lexmind.ocr.ocr_provider import OCRProvider
from lexmind.ocr.ocr_result import OCRPageResult, OCRResult

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeOCRProvider:
    """A configurable fake OCR provider for tests."""

    def __init__(
        self,
        name: str = "fake",
        supported: tuple[str, ...] = ("image/png", "application/pdf"),
        result: OCRResult | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._name = name
        self._supported = supported
        self._result = result
        self._raises = raises
        self.calls: list[tuple[bytes, str, str]] = []

    @property
    def name(self) -> str:
        return self._name

    def supports(self, mime_type: str) -> bool:
        return mime_type in self._supported

    def recognize(
        self,
        image_data: bytes,
        language: str = "",
        mime_type: str = "",
    ) -> OCRResult:
        self.calls.append((image_data, language, mime_type))
        if self._raises is not None:
            raise self._raises
        return self._result or OCRResult(
            text="hello",
            confidence=0.9,
            language=language,
            provider=self._name,
        )


def _sample_result() -> OCRResult:
    """Return a sample multi-page OCR result."""
    return OCRResult(
        text="page one\npage two",
        confidence=0.85,
        language="ron",
        provider="fake",
        pages=(
            OCRPageResult(page_number=1, text="page one", confidence=0.9),
            OCRPageResult(page_number=2, text="page two", confidence=0.8),
        ),
        metadata={"engine": "fake-1.0"},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage() -> MagicMock:
    """Provide a mock StorageManager."""
    mock = MagicMock()
    mock.load.return_value = b"image-bytes"
    return mock


@pytest.fixture()
def event_bus() -> MagicMock:
    """Provide a mock event bus."""
    return MagicMock()


@pytest.fixture()
def writer(storage: MagicMock) -> OCRArtifactWriter:
    """Provide an OCRArtifactWriter."""
    return OCRArtifactWriter(storage)


@pytest.fixture()
def dispatcher() -> OCRDispatcher:
    """Provide an OCRDispatcher with a registered fake provider."""
    d = OCRDispatcher()
    d.register(FakeOCRProvider())
    return d


@pytest.fixture()
def pipeline(
    dispatcher: OCRDispatcher,
    writer: OCRArtifactWriter,
    storage: MagicMock,
    event_bus: MagicMock,
) -> OCRPipeline:
    """Provide a fully wired OCRPipeline."""
    return OCRPipeline(
        dispatcher=dispatcher,
        artifact_writer=writer,
        storage_manager=storage,
        event_bus=event_bus,
    )


def _request(**overrides: object) -> OCRRequest:
    """Build an OCRRequest with sensible defaults."""
    params: dict[str, object] = {
        "workspace_id": "ws-1",
        "document_id": "doc-1",
        "source_uri": "storage://ws-1/originals/doc-1/scan.png",
        "language": "ron",
        "mime_type": "image/png",
    }
    params.update(overrides)
    return OCRRequest(**params)  # type: ignore[arg-type]


# ===========================================================================
# OCRResult / OCRPageResult
# ===========================================================================


class TestOCRResult:
    """Test OCR result value objects."""

    def test_defaults(self) -> None:
        """Default OCRResult is empty."""
        result = OCRResult()
        assert result.text == ""
        assert result.page_count == 0
        assert result.is_empty is True

    def test_page_count(self) -> None:
        """page_count reflects the number of pages."""
        result = _sample_result()
        assert result.page_count == 2

    def test_is_empty_false(self) -> None:
        """is_empty is False when text is present."""
        result = _sample_result()
        assert result.is_empty is False

    def test_invalid_confidence(self) -> None:
        """OCRResult rejects out-of-range confidence."""
        with pytest.raises(ValueError, match="confidence"):
            OCRResult(confidence=1.5)

    def test_page_invalid_confidence(self) -> None:
        """OCRPageResult rejects out-of-range confidence."""
        with pytest.raises(ValueError, match="confidence"):
            OCRPageResult(page_number=1, confidence=-0.1)

    def test_page_invalid_number(self) -> None:
        """OCRPageResult rejects negative page numbers."""
        with pytest.raises(ValueError, match="page_number"):
            OCRPageResult(page_number=-1)

    def test_frozen(self) -> None:
        """OCRResult is immutable."""
        result = OCRResult()
        with pytest.raises(AttributeError):
            result.text = "x"  # type: ignore[misc]


# ===========================================================================
# OCRDispatcher
# ===========================================================================


class TestOCRDispatcher:
    """Test provider selection."""

    def test_register_sets_default(self) -> None:
        """First registered provider becomes the default."""
        d = OCRDispatcher()
        d.register(FakeOCRProvider(name="p1"))
        assert d.default_provider == "p1"
        assert d.has_provider("p1")

    def test_select_by_name(self, dispatcher: OCRDispatcher) -> None:
        """select returns the provider matching the given name."""
        dispatcher.register(FakeOCRProvider(name="other"))
        provider = dispatcher.select(name="other")
        assert provider.name == "other"

    def test_select_default(self, dispatcher: OCRDispatcher) -> None:
        """select returns the default when no name is given."""
        provider = dispatcher.select()
        assert provider.name == "fake"

    def test_select_unknown_name_raises(
        self, dispatcher: OCRDispatcher
    ) -> None:
        """select raises for an unknown provider name."""
        with pytest.raises(OCRProviderNotFoundError):
            dispatcher.select(name="nonexistent")

    def test_select_by_mime_fallback(self) -> None:
        """select falls back to a provider supporting the MIME type."""
        d = OCRDispatcher()
        pdf_only = FakeOCRProvider(name="pdf", supported=("application/pdf",))
        img_only = FakeOCRProvider(name="img", supported=("image/png",))
        d.register(pdf_only)
        d.register(img_only)
        # default is pdf-only; request png -> fallback to img
        provider = d.select(mime_type="image/png")
        assert provider.name == "img"

    def test_select_no_provider_raises(self) -> None:
        """select raises when nothing can satisfy the request."""
        d = OCRDispatcher()
        with pytest.raises(OCRProviderNotFoundError):
            d.select(mime_type="image/png")

    def test_unregister(self, dispatcher: OCRDispatcher) -> None:
        """unregister removes a provider and updates the default."""
        dispatcher.unregister("fake")
        assert not dispatcher.has_provider("fake")
        assert dispatcher.default_provider is None

    def test_unregister_switches_default(self) -> None:
        """unregistering the default promotes another provider."""
        d = OCRDispatcher()
        d.register(FakeOCRProvider(name="p1"))
        d.register(FakeOCRProvider(name="p2"))
        d.unregister("p1")
        assert d.default_provider == "p2"

    def test_provider_satisfies_protocol(self) -> None:
        """FakeOCRProvider satisfies the OCRProvider protocol."""
        assert isinstance(FakeOCRProvider(), OCRProvider)

    def test_repr(self, dispatcher: OCRDispatcher) -> None:
        """__repr__ lists providers."""
        assert "fake" in repr(dispatcher)


# ===========================================================================
# OCRArtifactWriter
# ===========================================================================


class TestOCRArtifactWriter:
    """Test artifact persistence."""

    def test_write_returns_text_uri(
        self, writer: OCRArtifactWriter
    ) -> None:
        """write returns the plain-text artifact URI."""
        uri = writer.write("ws-1", "doc-1", _sample_result())
        assert uri == "storage://ws-1/ocr/doc-1/text.txt"

    def test_write_persists_text_and_json(
        self, writer: OCRArtifactWriter, storage: MagicMock
    ) -> None:
        """write stores both a text and a JSON artifact."""
        writer.write("ws-1", "doc-1", _sample_result())
        assert storage.save_text.call_count == 2

    def test_json_artifact_content(
        self, writer: OCRArtifactWriter, storage: MagicMock
    ) -> None:
        """The JSON artifact contains the structured result."""
        writer.write("ws-1", "doc-1", _sample_result())
        # Find the JSON call
        json_call = next(
            c for c in storage.save_text.call_args_list
            if c.args[0].endswith("result.json")
        )
        payload = json.loads(json_call.args[1])
        assert payload["provider"] == "fake"
        assert payload["page_count"] == 2
        assert len(payload["pages"]) == 2
        assert payload["metadata"] == {"engine": "fake-1.0"}

    def test_uri_builders(self, writer: OCRArtifactWriter) -> None:
        """URI builders produce the expected paths."""
        assert writer.build_text_uri("ws", "d") == "storage://ws/ocr/d/text.txt"
        assert (
            writer.build_json_uri("ws", "d")
            == "storage://ws/ocr/d/result.json"
        )

    def test_repr(self, writer: OCRArtifactWriter) -> None:
        """__repr__ is informative."""
        assert "OCRArtifactWriter" in repr(writer)


# ===========================================================================
# OCRRequest
# ===========================================================================


class TestOCRRequest:
    """Test OCR request validation."""

    def test_valid(self) -> None:
        """A complete request is accepted."""
        req = _request()
        assert req.workspace_id == "ws-1"

    def test_requires_workspace(self) -> None:
        """workspace_id is required."""
        with pytest.raises(ValueError, match="workspace_id"):
            _request(workspace_id="")

    def test_requires_document(self) -> None:
        """document_id is required."""
        with pytest.raises(ValueError, match="document_id"):
            _request(document_id="")

    def test_requires_source_uri(self) -> None:
        """source_uri is required."""
        with pytest.raises(ValueError, match="source_uri"):
            _request(source_uri="")


# ===========================================================================
# OCRPipeline
# ===========================================================================


class TestOCRPipeline:
    """Test the end-to-end orchestrator."""

    def test_successful_flow(self, pipeline: OCRPipeline) -> None:
        """A successful run returns an outcome with the artifact URI."""
        outcome = pipeline.execute(_request())
        assert isinstance(outcome, OCROutcome)
        assert outcome.provider == "fake"
        assert outcome.artifact_uri == "storage://ws-1/ocr/doc-1/text.txt"
        assert outcome.result.text == "hello"

    def test_loads_input_from_storage(
        self, pipeline: OCRPipeline, storage: MagicMock
    ) -> None:
        """The pipeline loads the source artifact via StorageManager."""
        pipeline.execute(_request())
        storage.load.assert_called_once_with(
            "storage://ws-1/originals/doc-1/scan.png"
        )

    def test_passes_data_to_provider(
        self, dispatcher: OCRDispatcher, writer: OCRArtifactWriter,
        storage: MagicMock, event_bus: MagicMock,
    ) -> None:
        """The loaded bytes and language are passed to the provider."""
        provider = FakeOCRProvider(name="probe")
        dispatcher.register(provider)
        pipe = OCRPipeline(dispatcher, writer, storage, event_bus)
        pipe.execute(_request(provider="probe"))
        assert provider.calls == [(b"image-bytes", "ron", "image/png")]

    def test_persists_result(
        self, pipeline: OCRPipeline, storage: MagicMock
    ) -> None:
        """The pipeline persists the OCR output."""
        pipeline.execute(_request())
        assert storage.save_text.call_count == 2

    def test_publishes_started_and_completed(
        self, pipeline: OCRPipeline, event_bus: MagicMock
    ) -> None:
        """A successful run publishes OCRStarted then OCRCompleted."""
        pipeline.execute(_request())
        published = [c.args[0] for c in event_bus.publish.call_args_list]
        assert any(isinstance(e, OCRStarted) for e in published)
        assert any(isinstance(e, OCRCompleted) for e in published)

    def test_completed_event_details(
        self, pipeline: OCRPipeline, event_bus: MagicMock
    ) -> None:
        """OCRCompleted carries the artifact URI and provider."""
        pipeline.execute(_request())
        completed = next(
            c.args[0] for c in event_bus.publish.call_args_list
            if isinstance(c.args[0], OCRCompleted)
        )
        assert completed.provider == "fake"
        assert completed.artifact_uri == "storage://ws-1/ocr/doc-1/text.txt"

    def test_failed_flow_raises_and_publishes(
        self, dispatcher: OCRDispatcher, writer: OCRArtifactWriter,
        storage: MagicMock, event_bus: MagicMock,
    ) -> None:
        """A provider error publishes OCRFailed and re-raises."""
        dispatcher.register(
            FakeOCRProvider(name="boom", raises=RuntimeError("engine crash"))
        )
        pipe = OCRPipeline(dispatcher, writer, storage, event_bus)
        with pytest.raises(RuntimeError, match="engine crash"):
            pipe.execute(_request(provider="boom"))
        failed = next(
            c.args[0] for c in event_bus.publish.call_args_list
            if isinstance(c.args[0], OCRFailed)
        )
        assert failed.error_message == "engine crash"
        assert failed.provider == "boom"

    def test_failed_flow_does_not_persist(
        self, dispatcher: OCRDispatcher, writer: OCRArtifactWriter,
        storage: MagicMock, event_bus: MagicMock,
    ) -> None:
        """A failed run does not write any artifact."""
        dispatcher.register(
            FakeOCRProvider(name="boom", raises=RuntimeError("crash"))
        )
        pipe = OCRPipeline(dispatcher, writer, storage, event_bus)
        with pytest.raises(RuntimeError):
            pipe.execute(_request(provider="boom"))
        storage.save_text.assert_not_called()

    def test_provider_selection_failure(
        self, writer: OCRArtifactWriter, storage: MagicMock,
        event_bus: MagicMock,
    ) -> None:
        """An empty dispatcher raises and publishes OCRFailed."""
        pipe = OCRPipeline(OCRDispatcher(), writer, storage, event_bus)
        with pytest.raises(OCRProviderNotFoundError):
            pipe.execute(_request(provider="missing"))
        assert any(
            isinstance(c.args[0], OCRFailed)
            for c in event_bus.publish.call_args_list
        )

    def test_no_event_bus(
        self, dispatcher: OCRDispatcher, writer: OCRArtifactWriter,
        storage: MagicMock,
    ) -> None:
        """The pipeline works without an event bus."""
        pipe = OCRPipeline(dispatcher, writer, storage, event_bus=None)
        outcome = pipe.execute(_request())
        assert outcome.provider == "fake"

    def test_repr(self, pipeline: OCRPipeline) -> None:
        """__repr__ is informative."""
        assert "OCRPipeline" in repr(pipeline)
