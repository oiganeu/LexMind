"""Workspace Repository -- interface and SQLite implementation.

Responsibilities:
    - CRUD operations for Workspace aggregates
    - Lookup by ID, UUID, and name
    - Pagination
    - Soft delete (marks workspace inactive, preserves data)
    - No business logic

Constraints:
    - Returns domain ``Workspace`` entities only.
    - No SQLAlchemy leaks outside this module.
    - Inject ``SessionManager`` via constructor.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from sqlalchemy import func

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.repositories.pagination import PageRequest, PageResult
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.models import WorkspaceRow

T = TypeVar("T")


@runtime_checkable
class WorkspaceRepository(Protocol[T]):
    """Interface for Workspace persistence.

    Every concrete workspace repository must implement this Protocol.
    The interface is kept minimal -- no business logic, no SQL, no ORM.
    """

    def create(self, workspace: T) -> T:
        """Persist a new workspace and return it."""

    def update(self, workspace: T) -> T:
        """Persist changes to an existing workspace and return it."""

    def get_by_id(self, workspace_id: str) -> T | None:
        """Retrieve a workspace by its primary key ID."""

    def get_by_id_any(self, workspace_id: str) -> T | None:
        """Retrieve a workspace by ID, including inactive ones."""

    def get_by_uuid(self, uuid: str) -> T | None:
        """Retrieve a workspace by its UUID (alias for get_by_id)."""

    def get_by_name(self, name: str) -> T | None:
        """Retrieve a workspace by its exact name."""

    def list_all(self) -> list[T]:
        """Return all active (non-deleted) workspaces."""

    def list_page(self, page_request: PageRequest) -> PageResult[T]:
        """Return a paginated list of active workspaces."""

    def delete(self, workspace_id: str) -> None:
        """Soft-delete a workspace by setting is_active=False."""

    def hard_delete(self, workspace_id: str) -> None:
        """Permanently remove a workspace from the store."""

    def exists(self, workspace_id: str) -> bool:
        """Return True if a workspace with the given ID exists."""

    def count(self) -> int:
        """Return the total number of active workspaces."""


class SqliteWorkspaceRepositoryImpl:
    """SQLite-backed implementation of ``WorkspaceRepository``.

    Uses the metadata subsystem for session management.  All queries
    filter out soft-deleted workspaces (``is_active=False``) unless
    explicitly requested.

    Soft delete: ``delete()`` sets ``is_active=False``.
    Hard delete: ``hard_delete()`` permanently removes the row.
    """

    def __init__(self, session_manager: SessionManager) -> None:  # noqa: F821
        """Initialise with a session manager.

        Args:
            session_manager: Provides context-managed SQLAlchemy sessions.
        """
        self._sm = session_manager

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, workspace: Workspace) -> Workspace:
        """Persist a new workspace and return it.

        Args:
            workspace: A domain Workspace entity.

        Returns:
            The same entity (with persisted state).
        """
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

    def update(self, workspace: Workspace) -> Workspace:
        """Persist changes to an existing workspace.

        Args:
            workspace: A domain Workspace entity with updated fields.

        Returns:
            The same entity.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
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

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Retrieve a workspace by its primary key ID.

        Returns None if not found or soft-deleted.
        """
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace_id)
            if row is None or not row.is_active:
                return None
            return self._to_domain(row)

    def get_by_id_any(self, workspace_id: str) -> Workspace | None:
        """Retrieve a workspace by ID, including inactive ones.

        Returns None only if the row does not exist.
        """
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace_id)
            if row is None:
                return None
            return self._to_domain(row)

    def get_by_uuid(self, uuid: str) -> Workspace | None:
        """Retrieve a workspace by its UUID.

        This is an alias for ``get_by_id`` since workspace IDs are UUIDs.
        """
        return self.get_by_id(uuid)

    def get_by_name(self, name: str) -> Workspace | None:
        """Retrieve a workspace by its exact name.

        Returns None if not found or soft-deleted.
        """
        with self._sm.session_scope() as session:
            row = (
                session.query(WorkspaceRow)
                .filter(WorkspaceRow.name == name, WorkspaceRow.is_active == True)  # noqa: E712
                .first()
            )
            return self._to_domain(row) if row else None

    # ------------------------------------------------------------------
    # Listing & Pagination
    # ------------------------------------------------------------------

    def list_all(self) -> list[Workspace]:
        """Return all active (non-deleted) workspaces."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(WorkspaceRow)
                .filter(WorkspaceRow.is_active == True)  # noqa: E712
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def list_page(self, page_request: PageRequest) -> PageResult[Workspace]:
        """Return a paginated list of active workspaces."""
        with self._sm.session_scope() as session:
            base = session.query(WorkspaceRow).filter(
                WorkspaceRow.is_active == True  # noqa: E712
            )
            total = base.count()
            rows = (
                base.offset(page_request.offset)
                .limit(page_request.limit)
                .all()
            )
            items = tuple(self._to_domain(r) for r in rows)
        return PageResult(
            items=items,
            total_count=total,
            page=page_request.page,
            page_size=page_request.page_size,
        )

    def count(self) -> int:
        """Return the total number of active workspaces."""
        with self._sm.session_scope() as session:
            return (
                session.query(func.count())
                .select_from(WorkspaceRow)
                .filter(WorkspaceRow.is_active == True)  # noqa: E712
                .scalar()
                or 0
            )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, workspace_id: str) -> None:
        """Soft-delete a workspace by setting ``is_active=False``.

        The workspace is preserved in the database but excluded from
        all active queries.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace_id)
            if row is None:
                raise EntityNotFoundError("Workspace", workspace_id)
            row.is_active = False
            from datetime import UTC, datetime

            row.updated_at = datetime.now(UTC)

    def hard_delete(self, workspace_id: str) -> None:
        """Permanently remove a workspace from the store.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace_id)
            if row is None:
                raise EntityNotFoundError("Workspace", workspace_id)
            session.delete(row)

    def exists(self, workspace_id: str) -> bool:
        """Return True if an active workspace with the given ID exists."""
        with self._sm.session_scope() as session:
            row = session.get(WorkspaceRow, workspace_id)
            return row is not None and row.is_active

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(row: WorkspaceRow) -> Workspace:
        """Convert an ORM row to a domain Workspace entity."""
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

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "SqliteWorkspaceRepositoryImpl()"
