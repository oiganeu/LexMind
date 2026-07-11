"""Tests for ArtifactRepository interface and SqliteArtifactRepositoryImpl.

Covers: CRUD, lookup by URI and type, document association,
versioning, latest version, delete, and no ORM leakage.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_state import ArtifactStatus
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.artifacts.artifact_version import ArtifactVersion
from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.session import SessionManager
from lexmind.repositories.artifact_repository import (
    ArtifactRepository,
    SqliteArtifactRepositoryImpl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db() -> Database:
    """Create an in-memory SQLite database for testing."""
    database = Database("sqlite:///:memory:")
    database.initialize()
    yield database
    database.dispose()


@pytest.fixture()
def sm(db: Database) -> SessionManager:
    """Create a SessionManager from the test database."""
    return SessionManager(db.engine)


@pytest.fixture()
def repo(sm: SessionManager) -> SqliteArtifactRepositoryImpl:
    """Create an SqliteArtifactRepositoryImpl for testing."""
    return SqliteArtifactRepositoryImpl(sm)


def _make_artifact(
    artifact_id: str = "art-1",
    workspace_id: str = "ws-1",
    document_id: str | None = None,
    artifact_type: ArtifactType = ArtifactType.ORIGINAL_DOCUMENT,
    status: ArtifactStatus = ArtifactStatus.REGISTERED,
    version: int = 1,
    uri: str = "storage://ws-1/originals/doc.pdf",
) -> Artifact:
    """Create a test Artifact entity."""
    artifact = Artifact(
        id=artifact_id,
        workspace_id=workspace_id,
        artifact_type=artifact_type,
        status=status,
        current_version=version,
        storage_uri=uri,
    )
    if document_id:
        artifact.document_id = document_id  # type: ignore[attr-defined]
    return artifact


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocol:
    """Verify that the implementation satisfies the Protocol."""

    def test_conforms_to_protocol(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """SqliteArtifactRepositoryImpl should be an ArtifactRepository."""
        assert isinstance(repo, ArtifactRepository)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreate:
    """Tests for artifact creation."""

    def test_create_persists_artifact(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should be retrievable by ID."""
        artifact = _make_artifact()
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.id == "art-1"
        assert loaded.artifact_type == ArtifactType.ORIGINAL_DOCUMENT

    def test_create_preserves_workspace(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve workspace_id."""
        artifact = _make_artifact(workspace_id="ws-99")
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.workspace_id == "ws-99"

    def test_create_preserves_uri(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve storage_uri."""
        artifact = _make_artifact(uri="storage://ws-1/data/test.pdf")
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.storage_uri == "storage://ws-1/data/test.pdf"

    def test_create_preserves_status(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve status."""
        artifact = _make_artifact(status=ArtifactStatus.AVAILABLE)
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.status == ArtifactStatus.AVAILABLE

    def test_create_preserves_checksum(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve checksum."""
        artifact = _make_artifact()
        artifact.checksum = "abc123"
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.checksum == "abc123"

    def test_create_preserves_producer(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve producer info."""
        artifact = _make_artifact()
        artifact.producer_module = "ocr_module"
        artifact.producer_version = "1.0.0"
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.producer_module == "ocr_module"
        assert loaded.producer_version == "1.0.0"

    def test_create_preserves_tags(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve tags."""
        artifact = _make_artifact()
        artifact.tags = ("legal", "contract")
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.tags == ("legal", "contract")

    def test_create_preserves_extra(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve extra dict."""
        artifact = _make_artifact()
        artifact.extra = {"key": "value"}
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.extra == {"key": "value"}

    def test_create_preserves_timestamps(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Created artifact should preserve timestamps."""
        artifact = _make_artifact()
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.created_at is not None
        assert loaded.updated_at is not None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    """Tests for artifact updates."""

    def test_update_persists_changes(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Updated fields should be persisted."""
        artifact = _make_artifact()
        repo.create(artifact)
        artifact.checksum = "new-checksum"
        artifact.storage_uri = "storage://ws-1/new-uri"
        repo.update(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.checksum == "new-checksum"
        assert loaded.storage_uri == "storage://ws-1/new-uri"

    def test_update_preserves_id(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """ID should remain unchanged after update."""
        artifact = _make_artifact()
        repo.create(artifact)
        artifact.checksum = "updated"
        repo.update(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.id == "art-1"

    def test_update_version(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Updating version should persist correctly."""
        artifact = _make_artifact()
        repo.create(artifact)
        artifact.current_version = 3
        repo.update(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.current_version == 3

    def test_update_status(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Status change should be persisted."""
        artifact = _make_artifact()
        repo.create(artifact)
        artifact.mark_available()
        repo.update(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.status == ArtifactStatus.AVAILABLE

    def test_update_not_found_raises(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Updating non-existent artifact should raise EntityNotFoundError."""
        artifact = _make_artifact(artifact_id="non-existent")
        with pytest.raises(EntityNotFoundError):
            repo.update(artifact)

    def test_update_timestamp(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Update should touch updated_at."""
        artifact = _make_artifact()
        repo.create(artifact)
        artifact.checksum = "trigger"
        repo.update(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.updated_at is not None


# ---------------------------------------------------------------------------
# Lookup by ID
# ---------------------------------------------------------------------------


class TestGetById:
    """Tests for lookup by ID."""

    def test_get_existing(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return artifact when it exists."""
        artifact = _make_artifact()
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.id == "art-1"

    def test_get_nonexistent_returns_none(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return None for non-existent ID."""
        loaded = repo.get_by_id("does-not-exist")
        assert loaded is None

    def test_get_deleted_returns_none(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return None for hard-deleted artifact."""
        artifact = _make_artifact()
        repo.create(artifact)
        repo.delete("art-1")
        loaded = repo.get_by_id("art-1")
        assert loaded is None


# ---------------------------------------------------------------------------
# Lookup by URI
# ---------------------------------------------------------------------------


class TestGetByUri:
    """Tests for lookup by storage URI."""

    def test_get_by_uri_existing(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return artifact matching the URI."""
        artifact = _make_artifact(uri="storage://ws-1/data/doc.pdf")
        repo.create(artifact)
        loaded = repo.get_by_uri("storage://ws-1/data/doc.pdf")
        assert loaded is not None
        assert loaded.storage_uri == "storage://ws-1/data/doc.pdf"

    def test_get_by_uri_nonexistent(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return None for non-existent URI."""
        loaded = repo.get_by_uri("storage://ws-1/nonexistent")
        assert loaded is None

    def test_get_by_uri_excludes_deleted(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return None for deleted artifact even if URI matches."""
        artifact = _make_artifact(uri="storage://ws-1/data/doc.pdf")
        repo.create(artifact)
        repo.delete("art-1")
        loaded = repo.get_by_uri("storage://ws-1/data/doc.pdf")
        assert loaded is None


# ---------------------------------------------------------------------------
# List by document
# ---------------------------------------------------------------------------


class TestListByDocument:
    """Tests for listing artifacts by document association."""

    def test_list_by_document(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return all artifacts associated with a document."""
        a1 = _make_artifact(artifact_id="art-1", document_id="doc-1")
        a2 = _make_artifact(artifact_id="art-2", document_id="doc-1")
        a3 = _make_artifact(artifact_id="art-3", document_id="doc-2")
        repo.create(a1)
        repo.create(a2)
        repo.create(a3)
        results = repo.list_by_document("doc-1")
        assert len(results) == 2
        ids = {a.id for a in results}
        assert ids == {"art-1", "art-2"}

    def test_list_by_document_empty(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return empty list for document with no artifacts."""
        results = repo.list_by_document("no-doc")
        assert results == []

    def test_list_by_document_excludes_deleted(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should exclude deleted artifacts."""
        a1 = _make_artifact(artifact_id="art-1", document_id="doc-1")
        a2 = _make_artifact(artifact_id="art-2", document_id="doc-1")
        repo.create(a1)
        repo.create(a2)
        repo.delete("art-1")
        results = repo.list_by_document("doc-1")
        assert len(results) == 1
        assert results[0].id == "art-2"


# ---------------------------------------------------------------------------
# List by type
# ---------------------------------------------------------------------------


class TestListByType:
    """Tests for listing artifacts by type."""

    def test_list_by_type(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return all artifacts of the given type."""
        a1 = _make_artifact(
            artifact_id="art-1",
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            workspace_id="ws-1",
        )
        a2 = _make_artifact(
            artifact_id="art-2",
            artifact_type=ArtifactType.OCR_TEXT,
            workspace_id="ws-1",
        )
        a3 = _make_artifact(
            artifact_id="art-3",
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            workspace_id="ws-2",
        )
        repo.create(a1)
        repo.create(a2)
        repo.create(a3)
        results = repo.list_by_type(ArtifactType.ORIGINAL_DOCUMENT)
        assert len(results) == 2

    def test_list_by_type_with_workspace(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should filter by workspace when provided."""
        a1 = _make_artifact(
            artifact_id="art-1",
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            workspace_id="ws-1",
        )
        a2 = _make_artifact(
            artifact_id="art-2",
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            workspace_id="ws-2",
        )
        repo.create(a1)
        repo.create(a2)
        results = repo.list_by_type(ArtifactType.ORIGINAL_DOCUMENT, workspace_id="ws-1")
        assert len(results) == 1
        assert results[0].id == "art-1"

    def test_list_by_type_empty(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return empty list when no artifacts match."""
        results = repo.list_by_type(ArtifactType.EMBEDDINGS)
        assert results == []

    def test_list_by_type_excludes_deleted(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should exclude deleted artifacts."""
        a1 = _make_artifact(
            artifact_id="art-1",
            artifact_type=ArtifactType.CHUNKS,
        )
        repo.create(a1)
        repo.delete("art-1")
        results = repo.list_by_type(ArtifactType.CHUNKS)
        assert results == []


# ---------------------------------------------------------------------------
# Latest version
# ---------------------------------------------------------------------------


class TestLatestVersion:
    """Tests for latest_version lookup."""

    def test_latest_version_single(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return the only artifact of given type in workspace."""
        artifact = _make_artifact(
            artifact_id="art-1",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=1,
        )
        repo.create(artifact)
        loaded = repo.latest_version("ws-1", ArtifactType.ENTITIES)
        assert loaded is not None
        assert loaded.id == "art-1"
        assert loaded.current_version == 1

    def test_latest_version_multiple(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return artifact with highest version number."""
        a1 = _make_artifact(
            artifact_id="art-1",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=1,
        )
        a2 = _make_artifact(
            artifact_id="art-2",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=3,
        )
        a3 = _make_artifact(
            artifact_id="art-3",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=2,
        )
        repo.create(a1)
        repo.create(a2)
        repo.create(a3)
        loaded = repo.latest_version("ws-1", ArtifactType.ENTITIES)
        assert loaded is not None
        assert loaded.id == "art-2"
        assert loaded.current_version == 3

    def test_latest_version_different_workspaces(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should only return from the specified workspace."""
        a1 = _make_artifact(
            artifact_id="art-1",
            workspace_id="ws-1",
            artifact_type=ArtifactType.REPORT,
            version=5,
        )
        a2 = _make_artifact(
            artifact_id="art-2",
            workspace_id="ws-2",
            artifact_type=ArtifactType.REPORT,
            version=1,
        )
        repo.create(a1)
        repo.create(a2)
        loaded = repo.latest_version("ws-2", ArtifactType.REPORT)
        assert loaded is not None
        assert loaded.id == "art-2"
        assert loaded.current_version == 1

    def test_latest_version_none_found(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should return None when no artifacts match."""
        loaded = repo.latest_version("ws-1", ArtifactType.SUMMARY)
        assert loaded is None

    def test_latest_version_excludes_deleted(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should skip deleted artifacts when finding latest."""
        a1 = _make_artifact(
            artifact_id="art-1",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=5,
        )
        a2 = _make_artifact(
            artifact_id="art-2",
            workspace_id="ws-1",
            artifact_type=ArtifactType.ENTITIES,
            version=2,
        )
        repo.create(a1)
        repo.create(a2)
        repo.delete("art-1")
        loaded = repo.latest_version("ws-1", ArtifactType.ENTITIES)
        assert loaded is not None
        assert loaded.id == "art-2"
        assert loaded.current_version == 2


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDelete:
    """Tests for hard delete."""

    def test_delete_removes_artifact(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Hard delete should remove the artifact from the store."""
        artifact = _make_artifact()
        repo.create(artifact)
        repo.delete("art-1")
        loaded = repo.get_by_id("art-1")
        assert loaded is None

    def test_delete_nonexistent_raises(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Deleting non-existent artifact should raise EntityNotFoundError."""
        with pytest.raises(EntityNotFoundError):
            repo.delete("does-not-exist")

    def test_delete_cannot_retrieve_by_uri(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """After delete, artifact should not be found by URI."""
        artifact = _make_artifact(uri="storage://ws-1/data/doc.pdf")
        repo.create(artifact)
        repo.delete("art-1")
        loaded = repo.get_by_uri("storage://ws-1/data/doc.pdf")
        assert loaded is None

    def test_delete_cannot_list_by_type(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """After delete, artifact should not appear in type listing."""
        artifact = _make_artifact(artifact_type=ArtifactType.THUMBNAIL)
        repo.create(artifact)
        repo.delete("art-1")
        results = repo.list_by_type(ArtifactType.THUMBNAIL)
        assert results == []


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


class TestVersioning:
    """Tests for version storage and retrieval."""

    def test_create_with_versions(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Should persist versions as JSON and restore on read."""
        artifact = _make_artifact()
        v1 = ArtifactVersion(
            artifact_id="art-1",
            version_number=1,
            checksum="sha1-aaa",
            producer_module="ocr",
            producer_version="1.0",
        )
        v2 = ArtifactVersion(
            artifact_id="art-1",
            version_number=2,
            checksum="sha1-bbb",
            producer_module="ocr",
            producer_version="1.1",
        )
        artifact.versions = [v1, v2]
        artifact.current_version = 2
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert len(loaded.versions) == 2
        assert loaded.versions[0].checksum == "sha1-aaa"
        assert loaded.versions[1].checksum == "sha1-bbb"
        assert loaded.versions[1].version_number == 2

    def test_update_with_new_version(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """New version added after creation should persist."""
        artifact = _make_artifact()
        v1 = ArtifactVersion(
            artifact_id="art-1",
            version_number=1,
            checksum="v1-check",
        )
        artifact.versions = [v1]
        repo.create(artifact)

        v2 = ArtifactVersion(
            artifact_id="art-1",
            version_number=2,
            checksum="v2-check",
        )
        artifact.versions = [v1, v2]
        artifact.current_version = 2
        repo.update(artifact)

        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert len(loaded.versions) == 2
        assert loaded.versions[1].checksum == "v2-check"

    def test_empty_versions(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Artifact with no versions should persist correctly."""
        artifact = _make_artifact()
        artifact.versions = []
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.versions == []

    def test_version_preserves_timestamps(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """Version timestamps should be preserved through serialization."""
        now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
        artifact = _make_artifact()
        v1 = ArtifactVersion(
            artifact_id="art-1",
            version_number=1,
            checksum="v1",
            created_at=now,
        )
        artifact.versions = [v1]
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert loaded is not None
        assert loaded.versions[0].created_at.year == 2025
        assert loaded.versions[0].created_at.month == 6


# ---------------------------------------------------------------------------
# No ORM leakage
# ---------------------------------------------------------------------------


class TestNoOrmLeakage:
    """Verify that all return types are domain entities, not ORM models."""

    def test_get_returns_domain_entity(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """get_by_id should return Artifact, not ArtifactRow."""
        artifact = _make_artifact()
        repo.create(artifact)
        loaded = repo.get_by_id("art-1")
        assert isinstance(loaded, Artifact)

    def test_get_by_uri_returns_domain_entity(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """get_by_uri should return Artifact, not ArtifactRow."""
        artifact = _make_artifact(uri="storage://ws-1/data/doc.pdf")
        repo.create(artifact)
        loaded = repo.get_by_uri("storage://ws-1/data/doc.pdf")
        assert isinstance(loaded, Artifact)

    def test_list_by_document_returns_domain_entities(
        self, repo: SqliteArtifactRepositoryImpl
    ) -> None:
        """list_by_document should return domain Artifact entities."""
        a1 = _make_artifact(artifact_id="art-1", document_id="doc-1")
        a2 = _make_artifact(artifact_id="art-2", document_id="doc-1")
        repo.create(a1)
        repo.create(a2)
        results = repo.list_by_document("doc-1")
        assert all(isinstance(a, Artifact) for a in results)

    def test_list_by_type_returns_domain_entities(
        self, repo: SqliteArtifactRepositoryImpl
    ) -> None:
        """list_by_type should return domain Artifact entities."""
        a1 = _make_artifact(artifact_id="art-1", artifact_type=ArtifactType.CHUNKS)
        repo.create(a1)
        results = repo.list_by_type(ArtifactType.CHUNKS)
        assert all(isinstance(a, Artifact) for a in results)

    def test_latest_version_returns_domain_entity(
        self, repo: SqliteArtifactRepositoryImpl
    ) -> None:
        """latest_version should return domain Artifact entity."""
        artifact = _make_artifact(artifact_type=ArtifactType.SUMMARY, workspace_id="ws-1")
        repo.create(artifact)
        loaded = repo.latest_version("ws-1", ArtifactType.SUMMARY)
        assert isinstance(loaded, Artifact)


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


class TestRepr:
    """Tests for string representations."""

    def test_repr(self, repo: SqliteArtifactRepositoryImpl) -> None:
        """repr should return a developer-friendly string."""
        assert "SqliteArtifactRepositoryImpl" in repr(repo)
