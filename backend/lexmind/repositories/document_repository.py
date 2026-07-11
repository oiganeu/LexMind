"""Document Repository -- interface and SQLite implementation.

Responsibilities:
    - CRUD operations for Document entities
    - Lookup by workspace, case, hash, status
    - Duplicate detection
    - No business logic

Constraints:
    - Returns domain ``Document`` entities only.
    - No SQLAlchemy leaks outside this module.
    - Inject ``SessionManager`` via constructor.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from sqlalchemy import func

from lexmind.domain.entities.document import Document
from lexmind.domain.enums.domain_enums import (
    DocumentStatus,
    DocumentTypeEnum,
    ProcessingStatus,
)
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.domain.value_objects.language import Language
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.models import DocumentRow

T = TypeVar("T")


@runtime_checkable
class DocumentRepository(Protocol[T]):
    """Interface for Document persistence.

    Every concrete document repository must implement this Protocol.
    """

    def create(self, document: T) -> T:
        """Persist a new document and return it."""

    def update(self, document: T) -> T:
        """Persist changes to an existing document and return it."""

    def get_by_id(self, document_id: str) -> T | None:
        """Retrieve a document by its primary key ID."""

    def find_by_hash(self, file_hash: str) -> T | None:
        """Find a document by its file hash (for duplicate detection)."""

    def find_by_workspace(self, workspace_id: str) -> list[T]:
        """Return all documents in a workspace."""

    def find_by_status(
        self, workspace_id: str, status: DocumentStatus
    ) -> list[T]:
        """Return documents by status within a workspace."""

    def delete(self, document_id: str) -> None:
        """Permanently remove a document from the store."""

    def exists(self, document_id: str) -> bool:
        """Return True if a document with the given ID exists."""

    def count(self, workspace_id: str) -> int:
        """Return the total number of documents in a workspace."""


class SqliteDocumentRepositoryImpl:
    """SQLite-backed implementation of ``DocumentRepository``.

    Uses the metadata subsystem for session management.
    """

    def __init__(self, session_manager: object) -> None:
        """Initialise with a session manager.

        Args:
            session_manager: Provides context-managed SQLAlchemy sessions.
        """
        self._sm = session_manager

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, document: Document) -> Document:
        """Persist a new document and return it."""
        row = DocumentRow(
            id=document.id,
            workspace_id=document.workspace_id,
            title=document.title,
            file_path=document.file_path.value if document.file_path else None,
            file_hash=document.file_hash.value if document.file_hash else None,
            mime_type=document.mime_type,
            document_type=document.document_type.value,
            status=document.status.value,
            processing_status=document.processing_status.value,
            language=document.language.value if document.language else None,
            case_ids=",".join(document.case_ids),
            tag_names=",".join(document.tag_names),
            version_count=document.version_count,
            is_duplicate=document.is_duplicate,
            has_ocr=document.has_ocr,
            has_embeddings=document.has_embeddings,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        with self._sm.session_scope() as session:
            session.add(row)
        return document

    def update(self, document: Document) -> Document:
        """Persist changes to an existing document."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, document.id)
            if row is None:
                raise EntityNotFoundError("Document", document.id)
            row.workspace_id = document.workspace_id
            row.title = document.title
            row.file_path = (
                document.file_path.value if document.file_path else None
            )
            row.file_hash = (
                document.file_hash.value if document.file_hash else None
            )
            row.mime_type = document.mime_type
            row.document_type = document.document_type.value
            row.status = document.status.value
            row.processing_status = document.processing_status.value
            row.language = (
                document.language.value if document.language else None
            )
            row.case_ids = ",".join(document.case_ids)
            row.tag_names = ",".join(document.tag_names)
            row.version_count = document.version_count
            row.is_duplicate = document.is_duplicate
            row.has_ocr = document.has_ocr
            row.has_embeddings = document.has_embeddings
            row.updated_at = document.updated_at
        return document

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_by_id(self, document_id: str) -> Document | None:
        """Retrieve a document by its primary key ID."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, document_id)
            if row is None:
                return None
            return self._to_domain(row)

    def find_by_hash(self, file_hash: str) -> Document | None:
        """Find a document by its file hash."""
        with self._sm.session_scope() as session:
            row = (
                session.query(DocumentRow)
                .filter(DocumentRow.file_hash == file_hash)
                .first()
            )
            return self._to_domain(row) if row else None

    def find_by_workspace(self, workspace_id: str) -> list[Document]:
        """Return all documents in a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(DocumentRow)
                .filter(DocumentRow.workspace_id == workspace_id)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def find_by_status(
        self, workspace_id: str, status: DocumentStatus
    ) -> list[Document]:
        """Return documents by status within a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(DocumentRow)
                .filter(
                    DocumentRow.workspace_id == workspace_id,
                    DocumentRow.status == status.value,
                )
                .all()
            )
            return [self._to_domain(r) for r in rows]

    # ------------------------------------------------------------------
    # Delete / Existence / Count
    # ------------------------------------------------------------------

    def delete(self, document_id: str) -> None:
        """Permanently remove a document from the store."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, document_id)
            if row is None:
                raise EntityNotFoundError("Document", document_id)
            session.delete(row)

    def exists(self, document_id: str) -> bool:
        """Return True if a document with the given ID exists."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, document_id)
            return row is not None

    def count(self, workspace_id: str) -> int:
        """Return the total number of documents in a workspace."""
        with self._sm.session_scope() as session:
            return (
                session.query(func.count())
                .select_from(DocumentRow)
                .filter(DocumentRow.workspace_id == workspace_id)
                .scalar()
                or 0
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(row: DocumentRow) -> Document:
        """Convert an ORM row to a domain Document entity."""
        file_path = FilePath(value=row.file_path) if row.file_path else None
        file_hash = FileHash(value=row.file_hash) if row.file_hash else None
        language = Language(value=row.language) if row.language else None
        case_ids = tuple(
            c for c in row.case_ids.split(",") if c
        ) if row.case_ids else ()
        tag_names = tuple(
            t for t in row.tag_names.split(",") if t
        ) if row.tag_names else ()

        return Document(
            id=row.id,
            workspace_id=row.workspace_id,
            title=row.title,
            file_path=file_path,
            file_hash=file_hash,
            mime_type=row.mime_type,
            document_type=DocumentTypeEnum(row.document_type),
            status=DocumentStatus(row.status),
            processing_status=ProcessingStatus(row.processing_status),
            language=language,
            case_ids=case_ids,
            tag_names=tag_names,
            version_count=row.version_count,
            is_duplicate=row.is_duplicate,
            has_ocr=row.has_ocr,
            has_embeddings=row.has_embeddings,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "SqliteDocumentRepositoryImpl()"
