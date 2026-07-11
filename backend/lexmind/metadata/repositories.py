"""Concrete repository implementations for the SQLite metadata store.

Each repository implements the corresponding domain repository Protocol,
translating between SQLAlchemy ORM models and domain entities.  Domain
code never sees these classes -- it interacts only through the Protocol.

Constraints:
    - No SQLAlchemy leaks into the domain layer.
    - Tuples (document_ids, etc.) are stored as comma-separated strings.
    - All sessions are context-managed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func

from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.models import CaseRow, DocumentRow, WorkspaceRow

if TYPE_CHECKING:

    from lexmind.metadata.session import SessionManager


def _parse_ids(raw: str) -> tuple[str, ...]:
    """Parse a comma-separated ID string into a tuple."""
    if not raw or not raw.strip():
        return ()
    return tuple(s.strip() for s in raw.split(",") if s.strip())


def _join_ids(ids: tuple[str, ...]) -> str:
    """Serialize a tuple of IDs to a comma-separated string."""
    return ",".join(ids)


# ---------------------------------------------------------------------------
# Workspace Repository
# ---------------------------------------------------------------------------


class SqliteWorkspaceRepository:
    """SQLite-backed implementation of WorkspaceRepository."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialise with a session manager.

        Args:
            session_manager: Provides context-managed sessions.
        """
        self._sm = session_manager

    def create(self, workspace: object) -> object:
        """Persist a new workspace and return it."""
        row = WorkspaceRow(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            owner_id=workspace.owner_id,
            is_active=workspace.is_active,
            document_count=workspace.document_count,
            case_count=workspace.case_count,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
        with self._sm.session_scope() as session:
            session.add(row)
        return workspace

    def update(self, workspace: object) -> object:
        """Persist changes to an existing workspace."""
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace.id)
            if row is None:
                raise EntityNotFoundError("Workspace", workspace.id)
            row.name = workspace.name
            row.description = workspace.description
            row.owner_id = workspace.owner_id
            row.is_active = workspace.is_active
            row.document_count = workspace.document_count
            row.case_count = workspace.case_count
            row.updated_at = workspace.updated_at
        return workspace

    def delete(self, entity_id: str) -> None:
        """Remove a workspace by ID."""
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, entity_id)
            if row is None:
                raise EntityNotFoundError("Workspace", entity_id)
            session.delete(row)

    def get(self, entity_id: str) -> object | None:
        """Retrieve a workspace by ID, or None if not found."""
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, entity_id)
            if row is None:
                return None
            return self._to_domain(row)

    def find(self, specification: object) -> list[object]:
        """Find all workspaces matching a specification (stub)."""
        return self.list_all()

    def find_one(self, specification: object) -> object | None:
        """Find a single workspace matching a specification (stub)."""
        return None

    def list_all(self) -> list[object]:
        """Return all workspaces."""
        with self._sm.session_scope() as session:
            rows = session.query(WorkspaceRow).all()
            return [self._to_domain(r) for r in rows]

    def list_page(self, page_request: object) -> object:
        """Return a paginated list of workspaces."""
        from lexmind.domain.repositories.pagination import PageResult

        page = getattr(page_request, "page", 1)
        page_size = getattr(page_request, "page_size", 20)
        offset = (page - 1) * page_size
        with self._sm.session_scope() as session:
            total = session.query(func.count()).select_from(WorkspaceRow).scalar() or 0
            rows = (
                session.query(WorkspaceRow)
                .offset(offset)
                .limit(page_size)
                .all()
            )
            items = tuple(self._to_domain(r) for r in rows)
        return PageResult(
            items=items,
            total_count=total,
            page=page,
            page_size=page_size,
        )

    def count(self) -> int:
        """Return the total number of workspaces."""
        with self._sm.session_scope() as session:
            return session.query(func.count()).select_from(WorkspaceRow).scalar() or 0

    def count_matching(self, specification: object) -> int:  # noqa: ARG002
        """Return the count matching a specification (stub)."""
        return self.count()

    def exists(self, entity_id: str) -> bool:
        """Return True if a workspace with the given ID exists."""
        with self._sm.session_scope() as session:
            return session.get(WorkspaceRow, entity_id) is not None

    def find_by_name(self, name: str) -> object | None:
        """Find a workspace by its exact name."""
        with self._sm.session_scope() as session:
            row = (
                session.query(WorkspaceRow)
                .filter(WorkspaceRow.name == name)
                .first()
            )
            return self._to_domain(row) if row else None

    def find_by_owner(self, owner_id: str) -> list[object]:
        """Find all workspaces owned by a user."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(WorkspaceRow)
                .filter(WorkspaceRow.owner_id == owner_id)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row: WorkspaceRow) -> object:
        """Convert an ORM row to a domain Workspace entity."""
        from lexmind.domain.entities.workspace import Workspace

        return Workspace(
            id=row.id,
            name=row.name,
            description=row.description,
            owner_id=row.owner_id,
            is_active=row.is_active,
            document_count=row.document_count,
            case_count=row.case_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


# ---------------------------------------------------------------------------
# Case Repository
# ---------------------------------------------------------------------------


class SqliteCaseRepository:
    """SQLite-backed implementation of CaseRepository."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialise with a session manager."""
        self._sm = session_manager

    def create(self, case: object) -> object:
        """Persist a new case and return it."""
        row = CaseRow(
            id=case.id,
            workspace_id=case.workspace_id,
            title=case.title,
            description=case.description,
            status=case.status.value if hasattr(case.status, "value") else str(case.status),
            document_ids=_join_ids(case.document_ids),
            evidence_ids=_join_ids(case.evidence_ids),
            person_ids=_join_ids(case.person_ids),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )
        with self._sm.session_scope() as session:
            session.add(row)
        return case

    def update(self, case: object) -> object:
        """Persist changes to an existing case."""
        with self._sm.session_scope() as session:
            row = session.get(CaseRow, case.id)
            if row is None:
                raise EntityNotFoundError("Case", case.id)
            row.workspace_id = case.workspace_id
            row.title = case.title
            row.description = case.description
            row.status = case.status.value if hasattr(case.status, "value") else str(case.status)
            row.document_ids = _join_ids(case.document_ids)
            row.evidence_ids = _join_ids(case.evidence_ids)
            row.person_ids = _join_ids(case.person_ids)
            row.updated_at = case.updated_at
        return case

    def delete(self, entity_id: str) -> None:
        """Remove a case by ID."""
        with self._sm.session_scope() as session:
            row = session.get(CaseRow, entity_id)
            if row is None:
                raise EntityNotFoundError("Case", entity_id)
            session.delete(row)

    def get(self, entity_id: str) -> object | None:
        """Retrieve a case by ID, or None if not found."""
        with self._sm.session_scope() as session:
            row = session.get(CaseRow, entity_id)
            if row is None:
                return None
            return self._to_domain(row)

    def find(self, specification: object) -> list[object]:
        """Find cases matching a specification (stub)."""
        return self.list_all()

    def find_one(self, specification: object) -> object | None:
        """Find a single case matching a specification (stub)."""
        return None

    def list_all(self) -> list[object]:
        """Return all cases."""
        with self._sm.session_scope() as session:
            rows = session.query(CaseRow).all()
            return [self._to_domain(r) for r in rows]

    def list_page(self, page_request: object) -> object:
        """Return a paginated list of cases."""
        from lexmind.domain.repositories.pagination import PageResult

        page = getattr(page_request, "page", 1)
        page_size = getattr(page_request, "page_size", 20)
        offset = (page - 1) * page_size
        with self._sm.session_scope() as session:
            total = session.query(func.count()).select_from(CaseRow).scalar() or 0
            rows = (
                session.query(CaseRow).offset(offset).limit(page_size).all()
            )
            items = tuple(self._to_domain(r) for r in rows)
        return PageResult(
            items=items,
            total_count=total,
            page=page,
            page_size=page_size,
        )

    def count(self) -> int:
        """Return the total number of cases."""
        with self._sm.session_scope() as session:
            return session.query(func.count()).select_from(CaseRow).scalar() or 0

    def count_matching(self, specification: object) -> int:  # noqa: ARG002
        """Return the count matching a specification (stub)."""
        return self.count()

    def exists(self, entity_id: str) -> bool:
        """Return True if a case with the given ID exists."""
        with self._sm.session_scope() as session:
            return session.get(CaseRow, entity_id) is not None

    def find_by_workspace(self, workspace_id: str) -> list[object]:
        """Find all cases in a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(CaseRow)
                .filter(CaseRow.workspace_id == workspace_id)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def find_by_status(self, status: object) -> list[object]:
        """Find all cases with a given status."""
        value = status.value if hasattr(status, "value") else str(status)
        with self._sm.session_scope() as session:
            rows = (
                session.query(CaseRow).filter(CaseRow.status == value).all()
            )
            return [self._to_domain(r) for r in rows]

    def find_by_title(self, workspace_id: str, title: str) -> object | None:
        """Find a case by title within a workspace."""
        with self._sm.session_scope() as session:
            row = (
                session.query(CaseRow)
                .filter(CaseRow.workspace_id == workspace_id)
                .filter(CaseRow.title == title)
                .first()
            )
            return self._to_domain(row) if row else None

    @staticmethod
    def _to_domain(row: CaseRow) -> object:
        """Convert an ORM row to a domain Case entity."""
        from lexmind.domain.entities.case import Case
        from lexmind.domain.enums.domain_enums import CaseStatus

        return Case(
            id=row.id,
            workspace_id=row.workspace_id,
            title=row.title,
            description=row.description,
            status=CaseStatus(row.status),
            document_ids=_parse_ids(row.document_ids),
            evidence_ids=_parse_ids(row.evidence_ids),
            person_ids=_parse_ids(row.person_ids),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


# ---------------------------------------------------------------------------
# Document Repository
# ---------------------------------------------------------------------------


class SqliteDocumentRepository:
    """SQLite-backed implementation of DocumentRepository."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialise with a session manager."""
        self._sm = session_manager

    def create(self, document: object) -> object:
        """Persist a new document and return it."""
        row = DocumentRow(
            id=document.id,
            workspace_id=document.workspace_id,
            title=document.title,
            file_path=document.file_path.value if document.file_path else None,
            file_hash=document.file_hash.value if document.file_hash else None,
            mime_type=document.mime_type,
            document_type=(
                document.document_type.value
                if hasattr(document.document_type, "value")
                else str(document.document_type)
            ),
            status=(
                document.status.value
                if hasattr(document.status, "value")
                else str(document.status)
            ),
            processing_status=(
                document.processing_status.value
                if hasattr(document.processing_status, "value")
                else str(document.processing_status)
            ),
            language=document.language.value if document.language else None,
            case_ids=_join_ids(document.case_ids),
            tag_names=_join_ids(document.tag_names),
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

    def update(self, document: object) -> object:
        """Persist changes to an existing document."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, document.id)
            if row is None:
                raise EntityNotFoundError("Document", document.id)
            row.workspace_id = document.workspace_id
            row.title = document.title
            row.file_path = document.file_path.value if document.file_path else None
            row.file_hash = document.file_hash.value if document.file_hash else None
            row.mime_type = document.mime_type
            row.document_type = (
                document.document_type.value
                if hasattr(document.document_type, "value")
                else str(document.document_type)
            )
            row.status = (
                document.status.value
                if hasattr(document.status, "value")
                else str(document.status)
            )
            row.processing_status = (
                document.processing_status.value
                if hasattr(document.processing_status, "value")
                else str(document.processing_status)
            )
            row.language = document.language.value if document.language else None
            row.case_ids = _join_ids(document.case_ids)
            row.tag_names = _join_ids(document.tag_names)
            row.version_count = document.version_count
            row.is_duplicate = document.is_duplicate
            row.has_ocr = document.has_ocr
            row.has_embeddings = document.has_embeddings
            row.updated_at = document.updated_at
        return document

    def delete(self, entity_id: str) -> None:
        """Remove a document by ID."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, entity_id)
            if row is None:
                raise EntityNotFoundError("Document", entity_id)
            session.delete(row)

    def get(self, entity_id: str) -> object | None:
        """Retrieve a document by ID, or None if not found."""
        with self._sm.session_scope() as session:
            row = session.get(DocumentRow, entity_id)
            if row is None:
                return None
            return self._to_domain(row)

    def find(self, specification: object) -> list[object]:
        """Find documents matching a specification (stub)."""
        return self.list_all()

    def find_one(self, specification: object) -> object | None:
        """Find a single document matching a specification (stub)."""
        return None

    def list_all(self) -> list[object]:
        """Return all documents."""
        with self._sm.session_scope() as session:
            rows = session.query(DocumentRow).all()
            return [self._to_domain(r) for r in rows]

    def list_page(self, page_request: object) -> object:
        """Return a paginated list of documents."""
        from lexmind.domain.repositories.pagination import PageResult

        page = getattr(page_request, "page", 1)
        page_size = getattr(page_request, "page_size", 20)
        offset = (page - 1) * page_size
        with self._sm.session_scope() as session:
            total = session.query(func.count()).select_from(DocumentRow).scalar() or 0
            rows = (
                session.query(DocumentRow).offset(offset).limit(page_size).all()
            )
            items = tuple(self._to_domain(r) for r in rows)
        return PageResult(
            items=items,
            total_count=total,
            page=page,
            page_size=page_size,
        )

    def count(self) -> int:
        """Return the total number of documents."""
        with self._sm.session_scope() as session:
            return session.query(func.count()).select_from(DocumentRow).scalar() or 0

    def count_matching(self, specification: object) -> int:  # noqa: ARG002
        """Return the count matching a specification (stub)."""
        return self.count()

    def exists(self, entity_id: str) -> bool:
        """Return True if a document with the given ID exists."""
        with self._sm.session_scope() as session:
            return session.get(DocumentRow, entity_id) is not None

    def find_by_workspace(self, workspace_id: str) -> list[object]:
        """Find all documents in a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(DocumentRow)
                .filter(DocumentRow.workspace_id == workspace_id)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def find_by_case(self, case_id: str) -> list[object]:
        """Find all documents linked to a case."""
        with self._sm.session_scope() as session:
            all_rows = session.query(DocumentRow).all()
            return [
                self._to_domain(r)
                for r in all_rows
                if case_id in _parse_ids(r.case_ids)
            ]

    def find_by_hash(self, file_hash: str) -> object | None:
        """Find a document by its file hash."""
        with self._sm.session_scope() as session:
            row = (
                session.query(DocumentRow)
                .filter(DocumentRow.file_hash == file_hash)
                .first()
            )
            return self._to_domain(row) if row else None

    def find_by_status(
        self, workspace_id: str, status: object
    ) -> list[object]:
        """Find documents by processing status within a workspace."""
        value = status.value if hasattr(status, "value") else str(status)
        with self._sm.session_scope() as session:
            rows = (
                session.query(DocumentRow)
                .filter(DocumentRow.workspace_id == workspace_id)
                .filter(DocumentRow.status == value)
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def find_duplicates(self, workspace_id: str) -> list[object]:
        """Find all documents marked as duplicates in a workspace."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(DocumentRow)
                .filter(DocumentRow.workspace_id == workspace_id)
                .filter(DocumentRow.is_duplicate == True)  # noqa: E712
                .all()
            )
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row: DocumentRow) -> object:
        """Convert an ORM row to a domain Document entity."""
        from lexmind.domain.entities.document import Document
        from lexmind.domain.enums.domain_enums import (
            DocumentStatus,
            DocumentTypeEnum,
            ProcessingStatus,
        )
        from lexmind.domain.value_objects.file import FileHash, FilePath
        from lexmind.domain.value_objects.language import Language

        return Document(
            id=row.id,
            workspace_id=row.workspace_id,
            title=row.title,
            file_path=FilePath(value=row.file_path) if row.file_path else None,
            file_hash=FileHash(value=row.file_hash) if row.file_hash else None,
            mime_type=row.mime_type,
            document_type=DocumentTypeEnum(row.document_type),
            status=DocumentStatus(row.status),
            processing_status=ProcessingStatus(row.processing_status),
            language=Language(value=row.language) if row.language else None,
            case_ids=_parse_ids(row.case_ids),
            tag_names=_parse_ids(row.tag_names),
            version_count=row.version_count,
            is_duplicate=row.is_duplicate,
            has_ocr=row.has_ocr,
            has_embeddings=row.has_embeddings,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
