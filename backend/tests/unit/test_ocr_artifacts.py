"""Tests for the OCR artifact generation layer (TASK-0025).

Covers:
    - OCRArtifactSerializer: text, result JSON, metadata JSON, checksum
    - OCRArtifactRepositoryAdapter: create, versioning, extra merge
    - OCRArtifactGenerator: persistence, registration, version increment,
      checksum validation
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_state import ArtifactStatus
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.ocr.artifacts.ocr_artifact_generator import (
    METADATA_FILENAME,
    RESULT_FILENAME,
    TEXT_FILENAME,
    TEXT_MEDIA_TYPE,
    OCRArtifactGenerator,
    OCRArtifactSet,
)
from lexmind.ocr.artifacts.ocr_artifact_repository_adapter import (
    OCRArtifactRepositoryAdapter,
)
from lexmind.ocr.artifacts.ocr_artifact_serializer import OCRArtifactSerializer
from lexmind.ocr.ocr_result import OCRPageResult, OCRResult

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeStorageManager:
    """In-memory storage facade capturing save_text calls."""

    def __init__(self) -> None:
        self.saved: dict[str, str] = {}

    def save_text(self, uri: str, text: str, encoding: str = "utf-8") -> None:
        self.saved[uri] = text


class FakeArtifactRepository:
    """In-memory artifact repository keyed by storage URI."""

    def __init__(self) -> None:
        self.by_uri: dict[str, Artifact] = {}
        self.created: list[Artifact] = []
        self.updated: list[Artifact] = []

    def get_by_uri(self, storage_uri: str) -> Artifact | None:
        return self.by_uri.get(storage_uri)

    def create(self, artifact: Artifact) -> Artifact:
        self.by_uri[artifact.storage_uri] = artifact
        self.created.append(artifact)
        return artifact

    def update(self, artifact: Artifact) -> Artifact:
        self.by_uri[artifact.storage_uri] = artifact
        self.updated.append(artifact)
        return artifact


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def result() -> OCRResult:
    return OCRResult(
        text="Hello world",
        confidence=0.9,
        language="ron",
        provider="tesseract",
        pages=(
            OCRPageResult(page_number=1, text="Hello world", confidence=0.9),
        ),
        metadata={"engine": "tesseract"},
    )


@pytest.fixture
def storage() -> FakeStorageManager:
    return FakeStorageManager()


@pytest.fixture
def repository() -> FakeArtifactRepository:
    return FakeArtifactRepository()


def _counter_id_factory() -> object:
    seq = iter(f"artifact-{i}" for i in range(1, 100))

    def factory() -> str:
        return next(seq)

    return factory


@pytest.fixture
def generator(
    storage: FakeStorageManager, repository: FakeArtifactRepository
) -> OCRArtifactGenerator:
    adapter = OCRArtifactRepositoryAdapter(
        repository, id_factory=_counter_id_factory()
    )
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)  # noqa: E731
    return OCRArtifactGenerator(storage, adapter, clock=clock)


# ---------------------------------------------------------------------------
# OCRArtifactSerializer
# ---------------------------------------------------------------------------


class TestOCRArtifactSerializer:
    def test_serialize_text_returns_plain_text(self, result: OCRResult) -> None:
        assert OCRArtifactSerializer().serialize_text(result) == "Hello world"

    def test_serialize_result_is_valid_json(self, result: OCRResult) -> None:
        payload = OCRArtifactSerializer().serialize_result(result)
        data = json.loads(payload)
        assert data["text"] == "Hello world"
        assert data["provider"] == "tesseract"
        assert data["page_count"] == 1
        assert data["pages"][0]["page_number"] == 1

    def test_serialize_metadata_is_valid_json(self, result: OCRResult) -> None:
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        payload = OCRArtifactSerializer().serialize_metadata(
            result, "doc-1", generated_at=ts
        )
        data = json.loads(payload)
        assert data["document_id"] == "doc-1"
        assert data["character_count"] == len("Hello world")
        assert data["generated_at"] == ts.isoformat()
        assert data["is_empty"] is False

    def test_serialize_metadata_defaults_timestamp(
        self, result: OCRResult
    ) -> None:
        payload = OCRArtifactSerializer().serialize_metadata(result, "doc-1")
        assert "generated_at" in json.loads(payload)

    def test_checksum_is_deterministic(self) -> None:
        serializer = OCRArtifactSerializer()
        assert serializer.checksum("abc") == serializer.checksum("abc")

    def test_checksum_differs_by_content(self) -> None:
        serializer = OCRArtifactSerializer()
        assert serializer.checksum("abc") != serializer.checksum("abd")

    def test_repr(self) -> None:
        assert repr(OCRArtifactSerializer()) == "OCRArtifactSerializer()"


# ---------------------------------------------------------------------------
# OCRArtifactRepositoryAdapter
# ---------------------------------------------------------------------------


class TestOCRArtifactRepositoryAdapter:
    def test_register_creates_new_artifact(
        self, repository: FakeArtifactRepository
    ) -> None:
        adapter = OCRArtifactRepositoryAdapter(
            repository, id_factory=_counter_id_factory()
        )
        artifact = adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-1",
            media_type=TEXT_MEDIA_TYPE,
        )
        assert artifact.id == "artifact-1"
        assert artifact.current_version == 1
        assert artifact.status is ArtifactStatus.AVAILABLE
        assert artifact.document_id == "doc-1"
        assert len(artifact.versions) == 1
        assert repository.created == [artifact]

    def test_register_second_uri_increments_version(
        self, repository: FakeArtifactRepository
    ) -> None:
        adapter = OCRArtifactRepositoryAdapter(
            repository, id_factory=_counter_id_factory()
        )
        adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-1",
            media_type=TEXT_MEDIA_TYPE,
        )
        second = adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-2",
            media_type=TEXT_MEDIA_TYPE,
        )
        assert second.current_version == 2
        assert second.checksum == "sum-2"
        assert len(second.versions) == 2
        assert repository.updated == [second]

    def test_register_merges_extra_on_version(
        self, repository: FakeArtifactRepository
    ) -> None:
        adapter = OCRArtifactRepositoryAdapter(
            repository, id_factory=_counter_id_factory()
        )
        adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-1",
            media_type=TEXT_MEDIA_TYPE,
            extra={"a": "1"},
        )
        second = adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-2",
            media_type=TEXT_MEDIA_TYPE,
            extra={"b": "2"},
        )
        assert second.extra == {"a": "1", "b": "2"}

    def test_default_id_factory_produces_unique_ids(
        self, repository: FakeArtifactRepository
    ) -> None:
        adapter = OCRArtifactRepositoryAdapter(repository)
        first = adapter.register(
            workspace_id="ws-1",
            document_id="doc-1",
            storage_uri="storage://ws-1/a.txt",
            checksum="sum-1",
            media_type=TEXT_MEDIA_TYPE,
        )
        second = adapter.register(
            workspace_id="ws-1",
            document_id="doc-2",
            storage_uri="storage://ws-1/b.txt",
            checksum="sum-1",
            media_type=TEXT_MEDIA_TYPE,
        )
        assert first.id != second.id

    def test_repr(self, repository: FakeArtifactRepository) -> None:
        adapter = OCRArtifactRepositoryAdapter(repository)
        assert repr(adapter) == "OCRArtifactRepositoryAdapter()"


# ---------------------------------------------------------------------------
# OCRArtifactGenerator
# ---------------------------------------------------------------------------


class TestOCRArtifactGenerator:
    def test_generate_returns_artifact_set(
        self, generator: OCRArtifactGenerator, result: OCRResult
    ) -> None:
        outcome = generator.generate("ws-1", "doc-1", result)
        assert isinstance(outcome, OCRArtifactSet)
        assert outcome.version == 1
        assert outcome.artifact_id == "artifact-1"

    def test_generate_persists_text_artifact(
        self,
        generator: OCRArtifactGenerator,
        storage: FakeStorageManager,
        result: OCRResult,
    ) -> None:
        outcome = generator.generate("ws-1", "doc-1", result)
        assert outcome.text_uri.endswith(TEXT_FILENAME)
        assert storage.saved[outcome.text_uri] == "Hello world"

    def test_generate_persists_json_artifacts(
        self,
        generator: OCRArtifactGenerator,
        storage: FakeStorageManager,
        result: OCRResult,
    ) -> None:
        outcome = generator.generate("ws-1", "doc-1", result)
        assert outcome.result_uri.endswith(RESULT_FILENAME)
        assert outcome.metadata_uri.endswith(METADATA_FILENAME)
        assert json.loads(storage.saved[outcome.result_uri])["text"] == "Hello world"
        assert json.loads(storage.saved[outcome.metadata_uri])["document_id"] == "doc-1"

    def test_generate_registers_primary_artifact(
        self,
        generator: OCRArtifactGenerator,
        repository: FakeArtifactRepository,
        result: OCRResult,
    ) -> None:
        generator.generate("ws-1", "doc-1", result)
        artifact = repository.created[0]
        assert artifact.artifact_type is ArtifactType.OCR_TEXT
        assert artifact.media_type == TEXT_MEDIA_TYPE
        assert artifact.extra["result_uri"].endswith(RESULT_FILENAME)
        assert artifact.extra["metadata_uri"].endswith(METADATA_FILENAME)

    def test_generate_version_increment(
        self, generator: OCRArtifactGenerator, result: OCRResult
    ) -> None:
        first = generator.generate("ws-1", "doc-1", result)
        second = generator.generate("ws-1", "doc-1", result)
        assert first.version == 1
        assert second.version == 2
        assert first.artifact_id == second.artifact_id

    def test_generate_checksum_validation(
        self,
        generator: OCRArtifactGenerator,
        storage: FakeStorageManager,
        result: OCRResult,
    ) -> None:
        outcome = generator.generate("ws-1", "doc-1", result)
        recomputed = OCRArtifactSerializer().checksum(
            storage.saved[outcome.text_uri]
        )
        assert recomputed == outcome.text_checksum

    def test_registered_artifact_checksum_matches(
        self,
        generator: OCRArtifactGenerator,
        repository: FakeArtifactRepository,
        result: OCRResult,
    ) -> None:
        outcome = generator.generate("ws-1", "doc-1", result)
        artifact = repository.created[0]
        assert artifact.validate_checksum(outcome.text_checksum)

    def test_build_uri_layout(self, generator: OCRArtifactGenerator) -> None:
        uri = generator.build_uri("ws-1", "doc-1", TEXT_FILENAME)
        assert uri == "storage://ws-1/artifacts/ocr/doc-1/ocr_text.txt"

    def test_default_serializer_used_when_omitted(
        self,
        storage: FakeStorageManager,
        repository: FakeArtifactRepository,
        result: OCRResult,
    ) -> None:
        adapter = OCRArtifactRepositoryAdapter(
            repository, id_factory=_counter_id_factory()
        )
        gen = OCRArtifactGenerator(storage, adapter)
        outcome = gen.generate("ws-1", "doc-1", result)
        assert outcome.text_checksum

    def test_repr(self, generator: OCRArtifactGenerator) -> None:
        assert repr(generator) == "OCRArtifactGenerator()"
