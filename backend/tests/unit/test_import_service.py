"""Tests for Import Service and Document Repository (TASK-0021).

Covers:
    - ImportService: import file, import folder, duplicate detection,
      unsupported format, events
    - SqliteDocumentRepositoryImpl: CRUD, find_by_hash, find_by_workspace,
      find_by_status, count, exists, delete
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lexmind.domain.entities.document import Document
from lexmind.domain.enums.domain_enums import (
    DocumentStatus,
)
from lexmind.domain.events.domain_events import DocumentImported
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.ingestion.import_events import ImportCompleted, ImportStarted
from lexmind.ingestion.import_service import ImportService
from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.session import SessionManager
from lexmind.repositories.document_repository import (
    DocumentRepository,
    SqliteDocumentRepositoryImpl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db() -> Database:
    """Provide an in-memory Database."""
    d = Database("sqlite:///:memory:")
    d.initialize()
    yield d
    d.dispose()


@pytest.fixture()
def session_mgr(db: Database) -> SessionManager:
    """Provide a SessionManager."""
    return SessionManager(db.engine)


@pytest.fixture()
def doc_repo(
    session_mgr: SessionManager,
) -> SqliteDocumentRepositoryImpl:
    """Provide a DocumentRepository."""
    return SqliteDocumentRepositoryImpl(session_mgr)


@pytest.fixture()
def storage() -> MagicMock:
    """Provide a mock StorageManager."""
    return MagicMock()


@pytest.fixture()
def event_bus() -> MagicMock:
    """Provide a mock event bus."""
    return MagicMock()


@pytest.fixture()
def import_svc(
    storage: MagicMock,
    doc_repo: SqliteDocumentRepositoryImpl,
    event_bus: MagicMock,
) -> ImportService:
    """Provide an ImportService."""
    return ImportService(
        workspace_id="ws-1",
        storage_manager=storage,
        document_repository=doc_repo,
        event_bus=event_bus,
    )


# ===================================================================
# Document Repository
# ===================================================================


class TestDocumentRepository:
    """Tests for SqliteDocumentRepositoryImpl."""

    def _make_doc(
        self,
        doc_id: str = "doc-1",
        workspace_id: str = "ws-1",
        title: str = "Test Doc",
        file_hash: str = "a" * 40,
        status: DocumentStatus = DocumentStatus.IMPORTED,
    ) -> Document:
        """Helper: create a Document entity."""
        return Document(
            id=doc_id,
            workspace_id=workspace_id,
            title=title,
            file_hash=FileHash(value=file_hash),
            file_path=FilePath(value="test.pdf"),
            mime_type="application/pdf",
            status=status,
        )

    def test_conforms_to_protocol(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """SqliteDocumentRepositoryImpl should be a DocumentRepository."""
        assert isinstance(doc_repo, DocumentRepository)

    def test_create_and_get(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """Created document should be retrievable by ID."""
        doc = self._make_doc()
        doc_repo.create(doc)
        loaded = doc_repo.get_by_id("doc-1")
        assert loaded is not None
        assert loaded.id == "doc-1"
        assert loaded.title == "Test Doc"

    def test_get_nonexistent(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """get_by_id returns None for non-existent document."""
        assert doc_repo.get_by_id("nope") is None

    def test_find_by_hash(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """find_by_hash should locate document by file hash."""
        doc = self._make_doc(file_hash="b" * 40)
        doc_repo.create(doc)
        loaded = doc_repo.find_by_hash("b" * 40)
        assert loaded is not None
        assert loaded.id == "doc-1"

    def test_find_by_hash_not_found(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """find_by_hash returns None when no match."""
        assert doc_repo.find_by_hash("c" * 40) is None

    def test_find_by_workspace(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """find_by_workspace returns all docs in workspace."""
        doc_repo.create(self._make_doc(doc_id="d1", workspace_id="ws-1"))
        doc_repo.create(self._make_doc(doc_id="d2", workspace_id="ws-1"))
        doc_repo.create(self._make_doc(doc_id="d3", workspace_id="ws-2"))
        result = doc_repo.find_by_workspace("ws-1")
        assert len(result) == 2

    def test_find_by_status(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """find_by_status filters by status."""
        doc_repo.create(self._make_doc(
            doc_id="d1",
            status=DocumentStatus.IMPORTED,
        ))
        doc_repo.create(self._make_doc(
            doc_id="d2",
            status=DocumentStatus.PROCESSED,
        ))
        result = doc_repo.find_by_status("ws-1", DocumentStatus.IMPORTED)
        assert len(result) == 1
        assert result[0].id == "d1"

    def test_update(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """update() should persist changes."""
        doc = self._make_doc()
        doc_repo.create(doc)
        doc.title = "Updated Title"
        doc_repo.update(doc)
        loaded = doc_repo.get_by_id("doc-1")
        assert loaded is not None
        assert loaded.title == "Updated Title"

    def test_update_not_found(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """update() raises EntityNotFoundError for missing doc."""
        doc = self._make_doc(doc_id="missing")
        with pytest.raises(EntityNotFoundError):
            doc_repo.update(doc)

    def test_delete(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """delete() removes the document permanently."""
        doc = self._make_doc()
        doc_repo.create(doc)
        doc_repo.delete("doc-1")
        assert doc_repo.get_by_id("doc-1") is None

    def test_delete_not_found(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """delete() raises EntityNotFoundError for missing doc."""
        with pytest.raises(EntityNotFoundError):
            doc_repo.delete("missing")

    def test_exists(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """exists() returns True for existing document."""
        doc = self._make_doc()
        doc_repo.create(doc)
        assert doc_repo.exists("doc-1") is True

    def test_exists_not_found(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """exists() returns False for non-existent document."""
        assert doc_repo.exists("nope") is False

    def test_count(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """count() returns total documents in workspace."""
        doc_repo.create(self._make_doc(doc_id="d1"))
        doc_repo.create(self._make_doc(doc_id="d2"))
        doc_repo.create(self._make_doc(
            doc_id="d3", workspace_id="ws-2"
        ))
        assert doc_repo.count("ws-1") == 2

    def test_returns_domain_entities(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """All return types should be domain Document entities."""
        doc = self._make_doc()
        doc_repo.create(doc)
        loaded = doc_repo.get_by_id("doc-1")
        assert isinstance(loaded, Document)

    def test_repr(
        self, doc_repo: SqliteDocumentRepositoryImpl
    ) -> None:
        """repr should return a developer-friendly string."""
        assert "SqliteDocumentRepositoryImpl" in repr(doc_repo)


# ===================================================================
# Import Service
# ===================================================================


class TestImportService:
    """Tests for ImportService."""

    def test_import_file(
        self,
        import_svc: ImportService,
        doc_repo: SqliteDocumentRepositoryImpl,
        storage: MagicMock,
    ) -> None:
        """import_file should create a document and store the file."""
        data = b"hello world"
        doc = import_svc.import_file("contract.pdf", data)
        assert isinstance(doc, Document)
        assert doc.workspace_id == "ws-1"
        assert doc.status == DocumentStatus.IMPORTED
        assert doc.file_hash is not None
        storage.save.assert_called_once()

    def test_import_file_persists_metadata(
        self,
        import_svc: ImportService,
        doc_repo: SqliteDocumentRepositoryImpl,
    ) -> None:
        """import_file should persist document metadata."""
        import_svc.import_file("report.txt", b"content")
        docs = doc_repo.find_by_workspace("ws-1")
        assert len(docs) == 1
        assert docs[0].title == "report"

    def test_import_file_uses_filename_as_title(
        self,
        import_svc: ImportService,
    ) -> None:
        """import_file should use filename stem as title."""
        doc = import_svc.import_file("my_document.pdf", b"data")
        assert doc.title == "my_document"

    def test_import_file_custom_title(
        self,
        import_svc: ImportService,
    ) -> None:
        """import_file should use provided title when given."""
        doc = import_svc.import_file(
            "file.pdf", b"data", title="Custom Title"
        )
        assert doc.title == "Custom Title"

    def test_import_file_unsupported_format(
        self,
        import_svc: ImportService,
    ) -> None:
        """import_file raises ValueError for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported"):
            import_svc.import_file("file.exe", b"data")

    def test_import_file_publishes_events(
        self,
        import_svc: ImportService,
        event_bus: MagicMock,
    ) -> None:
        """import_file should publish ImportStarted and ImportCompleted."""
        import_svc.import_file("doc.pdf", b"data")
        calls = [c[0][0] for c in event_bus.publish.call_args_list]
        assert any(isinstance(e, ImportStarted) for e in calls)
        assert any(isinstance(e, ImportCompleted) for e in calls)

    def test_import_file_publishes_document_imported(
        self,
        import_svc: ImportService,
        event_bus: MagicMock,
    ) -> None:
        """import_file should publish DocumentImported."""
        import_svc.import_file("doc.pdf", b"data")
        calls = [c[0][0] for c in event_bus.publish.call_args_list]
        assert any(isinstance(e, DocumentImported) for e in calls)

    def test_import_file_stores_via_storage_manager(
        self,
        import_svc: ImportService,
        storage: MagicMock,
    ) -> None:
        """import_file should store the file via StorageManager."""
        data = b"test content"
        import_svc.import_file("test.pdf", data)
        storage.save.assert_called_once()
        call_args = storage.save.call_args
        uri = call_args[0][0]
        assert uri.startswith("storage://ws-1/originals/")
        assert call_args[0][1] == data

    def test_import_file_duplicate_detection(
        self,
        import_svc: ImportService,
        doc_repo: SqliteDocumentRepositoryImpl,
    ) -> None:
        """import_file should detect duplicates by hash."""
        data = b"same content"
        doc1 = import_svc.import_file("file1.pdf", data)
        doc2 = import_svc.import_file("file2.pdf", data)
        assert doc1.is_duplicate is False
        assert doc2.is_duplicate is True

    def test_import_file_sets_correct_mime_type(
        self,
        import_svc: ImportService,
    ) -> None:
        """import_file should set MIME type based on extension."""
        doc_pdf = import_svc.import_file("doc.pdf", b"data")
        doc_png = import_svc.import_file("img.png", b"data")
        doc_txt = import_svc.import_file("readme.txt", b"data")
        assert doc_pdf.mime_type == "application/pdf"
        assert doc_png.mime_type == "image/png"
        assert doc_txt.mime_type == "text/plain"

    def test_import_folder(
        self,
        import_svc: ImportService,
        doc_repo: SqliteDocumentRepositoryImpl,
    ) -> None:
        """import_folder should import multiple files."""
        files = {
            "a.pdf": b"content a",
            "b.txt": b"content b",
        }
        docs = import_svc.import_folder("/docs", files)
        assert len(docs) == 2
        all_docs = doc_repo.find_by_workspace("ws-1")
        assert len(all_docs) == 2

    def test_import_folder_publishes_events(
        self,
        import_svc: ImportService,
        event_bus: MagicMock,
    ) -> None:
        """import_folder should publish events for each file."""
        files = {"a.pdf": b"data"}
        import_svc.import_folder("/docs", files)
        calls = [c[0][0] for c in event_bus.publish.call_args_list]
        started = [e for e in calls if isinstance(e, ImportStarted)]
        completed = [e for e in calls if isinstance(e, ImportCompleted)]
        assert len(started) == 1
        assert len(completed) == 1

    def test_import_file_no_event_bus(
        self,
        storage: MagicMock,
        doc_repo: SqliteDocumentRepositoryImpl,
    ) -> None:
        """import_file should succeed without an event bus."""
        svc = ImportService(
            workspace_id="ws-1",
            storage_manager=storage,
            document_repository=doc_repo,
            event_bus=None,
        )
        doc = svc.import_file("doc.pdf", b"data")
        assert doc.status == DocumentStatus.IMPORTED

    def test_import_completed_contains_metadata(
        self,
        import_svc: ImportService,
        event_bus: MagicMock,
    ) -> None:
        """ImportCompleted event should contain document metadata."""
        import_svc.import_file("test.pdf", b"data")
        calls = [c[0][0] for c in event_bus.publish.call_args_list]
        completed = [e for e in calls if isinstance(e, ImportCompleted)]
        assert len(completed) == 1
        event = completed[0]
        assert event.workspace_id == "ws-1"
        assert event.file_path == "test.pdf"
        assert event.is_duplicate is False
