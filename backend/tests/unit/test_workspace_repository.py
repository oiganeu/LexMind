"""Unit tests for Workspace Repository (TASK-0018).

Covers:
    - CRUD operations (create, update, get_by_id, get_by_name)
    - UUID lookup (get_by_uuid)
    - Soft delete (delete sets is_active=False, hard_delete removes)
    - Pagination
    - Duplicate name validation
    - No ORM leakage outside repository
"""

from __future__ import annotations

import pytest

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.repositories.pagination import PageRequest
from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.session import SessionManager
from lexmind.repositories.workspace_repository import (
    SqliteWorkspaceRepositoryImpl,
    WorkspaceRepository,
)

# ======================================================================
# Fixtures
# ======================================================================


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
def repo(session_mgr: SessionManager) -> SqliteWorkspaceRepositoryImpl:
    """Provide a WorkspaceRepository."""
    return SqliteWorkspaceRepositoryImpl(session_mgr)


def _make_ws(
    ws_id: str = "ws-1",
    name: str = "Test Workspace",
    owner_id: str = "user-1",
) -> Workspace:
    """Create a domain Workspace entity."""
    return Workspace(id=ws_id, name=name, owner_id=owner_id)


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:
    """Verify the implementation satisfies the Protocol."""

    def test_is_protocol_instance(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert isinstance(repo, WorkspaceRepository)


# ======================================================================
# CRUD -- Create
# ======================================================================


class TestCreate:
    """Tests for workspace creation."""

    def test_create_and_retrieve(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded is not None
        assert loaded.name == "Test Workspace"
        assert loaded.owner_id == "user-1"
        assert loaded.is_active is True

    def test_create_persists_all_fields(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        ws.description = "A workspace for testing"
        ws.document_count = 5
        ws.case_count = 3
        repo.create(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded.description == "A workspace for testing"
        assert loaded.document_count == 5
        assert loaded.case_count == 3

    def test_create_returns_same_entity(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        result = repo.create(ws)
        assert result.id == ws.id
        assert result.name == ws.name


# ======================================================================
# CRUD -- Update
# ======================================================================


class TestUpdate:
    """Tests for workspace updates."""

    def test_update_name(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        ws.name = "Updated Name"
        repo.update(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded.name == "Updated Name"

    def test_update_description(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        ws.description = "New description"
        repo.update(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded.description == "New description"

    def test_update_counters(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        ws.document_count = 10
        ws.case_count = 7
        repo.update(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded.document_count == 10
        assert loaded.case_count == 7

    def test_update_not_found(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(ws_id="nonexistent")
        with pytest.raises(EntityNotFoundError):
            repo.update(ws)

    def test_update_timestamp(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        ws.description = "trigger touch"
        ws.touch()
        repo.update(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded is not None
        assert loaded.updated_at is not None


# ======================================================================
# Lookup -- get_by_id
# ======================================================================


class TestGetById:
    """Tests for ID-based lookup."""

    def test_get_existing(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        loaded = repo.get_by_id(ws.id)
        assert loaded is not None
        assert loaded.id == ws.id

    def test_get_nonexistent(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.get_by_id("nonexistent") is None

    def test_get_soft_deleted_returns_none(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)
        assert repo.get_by_id(ws.id) is None


# ======================================================================
# Lookup -- get_by_uuid
# ======================================================================


class TestGetByUuid:
    """Tests for UUID-based lookup."""

    def test_get_by_uuid(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(ws_id="uuid-abc-123")
        repo.create(ws)
        loaded = repo.get_by_uuid("uuid-abc-123")
        assert loaded is not None
        assert loaded.id == "uuid-abc-123"

    def test_get_by_uuid_nonexistent(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.get_by_uuid("nope") is None

    def test_get_by_uuid_soft_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(ws_id="uuid-del")
        repo.create(ws)
        repo.delete(ws.id)
        assert repo.get_by_uuid("uuid-del") is None


# ======================================================================
# Lookup -- get_by_name
# ======================================================================


class TestGetByName:
    """Tests for name-based lookup."""

    def test_get_by_name(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(name="Unique Workspace")
        repo.create(ws)
        loaded = repo.get_by_name("Unique Workspace")
        assert loaded is not None
        assert loaded.name == "Unique Workspace"

    def test_get_by_name_nonexistent(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.get_by_name("Nope") is None

    def test_get_by_name_soft_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(name="Deleted WS")
        repo.create(ws)
        repo.delete(ws.id)
        assert repo.get_by_name("Deleted WS") is None

    def test_get_by_name_is_exact(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws(name="Exact Name")
        repo.create(ws)
        assert repo.get_by_name("Exact") is None
        assert repo.get_by_name("Exact Name ") is None


# ======================================================================
# Listing
# ======================================================================


class TestListAll:
    """Tests for listing workspaces."""

    def test_list_all(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws("ws-1", "A"))
        repo.create(_make_ws("ws-2", "B"))
        repo.create(_make_ws("ws-3", "C"))
        result = repo.list_all()
        assert len(result) == 3

    def test_list_excludes_soft_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws("ws-1", "Active"))
        repo.create(_make_ws("ws-2", "Deleted"))
        repo.delete("ws-2")
        result = repo.list_all()
        assert len(result) == 1
        assert result[0].name == "Active"

    def test_list_empty(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.list_all() == []


# ======================================================================
# Pagination
# ======================================================================


class TestPagination:
    """Tests for paginated listing."""

    def test_pagination_basic(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        for i in range(10):
            repo.create(_make_ws(f"ws-{i}", f"W{i}"))
        page = repo.list_page(PageRequest(page=1, page_size=3))
        assert len(page.items) == 3
        assert page.total_count == 10
        assert page.has_next is True
        assert page.has_previous is False

    def test_pagination_last_page(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        for i in range(5):
            repo.create(_make_ws(f"ws-{i}", f"W{i}"))
        page = repo.list_page(PageRequest(page=3, page_size=2))
        assert len(page.items) == 1
        assert page.has_next is False

    def test_pagination_excludes_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        for i in range(5):
            repo.create(_make_ws(f"ws-{i}", f"W{i}"))
        repo.delete("ws-0")
        repo.delete("ws-1")
        page = repo.list_page(PageRequest(page=1, page_size=10))
        assert page.total_count == 3
        assert len(page.items) == 3

    def test_pagination_empty(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        page = repo.list_page(PageRequest(page=1, page_size=10))
        assert page.total_count == 0
        assert len(page.items) == 0


# ======================================================================
# Count
# ======================================================================


class TestCount:
    """Tests for counting workspaces."""

    def test_count(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws("ws-1", "A"))
        repo.create(_make_ws("ws-2", "B"))
        assert repo.count() == 2

    def test_count_excludes_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws("ws-1", "A"))
        repo.create(_make_ws("ws-2", "B"))
        repo.delete("ws-2")
        assert repo.count() == 1

    def test_count_empty(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.count() == 0


# ======================================================================
# Exists
# ======================================================================


class TestExists:
    """Tests for existence check."""

    def test_exists(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        assert repo.exists(ws.id) is True

    def test_exists_nonexistent(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert repo.exists("nope") is False

    def test_exists_soft_deleted(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)
        assert repo.exists(ws.id) is False


# ======================================================================
# Soft Delete
# ======================================================================


class TestSoftDelete:
    """Tests for soft delete behavior."""

    def test_soft_delete(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)
        # Should be invisible to all queries
        assert repo.get_by_id(ws.id) is None
        assert repo.get_by_name(ws.name) is None
        assert repo.exists(ws.id) is False
        assert repo.count() == 0

    def test_soft_delete_preserves_row(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)
        # Verify the row still exists in the database (not hard deleted)
        from lexmind.metadata.models import WorkspaceRow

        with repo._sm.session_scope() as session:
            row = session.get(WorkspaceRow, ws.id)
            assert row is not None
            assert row.is_active is False

    def test_soft_delete_not_found(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        with pytest.raises(EntityNotFoundError):
            repo.delete("nonexistent")

    def test_soft_delete_updates_timestamp(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)
        from lexmind.metadata.models import WorkspaceRow

        with repo._sm.session_scope() as session:
            row = session.get(WorkspaceRow, ws.id)
            assert row is not None
            assert row.updated_at is not None


# ======================================================================
# Hard Delete
# ======================================================================


class TestHardDelete:
    """Tests for hard delete behavior."""

    def test_hard_delete_removes_row(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.hard_delete(ws.id)
        # Verify the row is gone
        from lexmind.metadata.models import WorkspaceRow

        with repo._sm.session_scope() as session:
            row = session.get(WorkspaceRow, ws.id)
            assert row is None

    def test_hard_delete_not_found(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        with pytest.raises(EntityNotFoundError):
            repo.hard_delete("nonexistent")

    def test_hard_delete_after_soft_delete(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        repo.delete(ws.id)  # soft delete first
        repo.hard_delete(ws.id)  # then hard delete
        from lexmind.metadata.models import WorkspaceRow

        with repo._sm.session_scope() as session:
            row = session.get(WorkspaceRow, ws.id)
            assert row is None


# ======================================================================
# Duplicate Name Validation
# ======================================================================


class TestDuplicateName:
    """Tests for name uniqueness constraints."""

    def test_duplicate_name_raises_integrity_error(
        self, repo: SqliteWorkspaceRepositoryImpl
    ) -> None:
        from sqlalchemy.exc import IntegrityError

        repo.create(_make_ws("ws-1", "Same Name"))
        with pytest.raises(IntegrityError):
            repo.create(_make_ws("ws-2", "Same Name"))

    def test_soft_deleted_name_still_enforces_uniqueness(
        self, repo: SqliteWorkspaceRepositoryImpl
    ) -> None:

        repo.create(_make_ws("ws-1", "My Workspace"))
        repo.hard_delete("ws-1")  # hard delete to free the name
        repo.create(_make_ws("ws-2", "My Workspace"))
        loaded = repo.get_by_name("My Workspace")
        assert loaded is not None
        assert loaded.id == "ws-2"


# ======================================================================
# No ORM Leakage
# ======================================================================


class TestNoOrmLeakage:
    """Verify no SQLAlchemy types leak into the domain."""

    def test_list_returns_domain_entities(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws())
        result = repo.list_all()
        for ws in result:
            assert isinstance(ws, Workspace)

    def test_get_returns_domain_entity(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        ws = _make_ws()
        repo.create(ws)
        loaded = repo.get_by_id(ws.id)
        assert isinstance(loaded, Workspace)

    def test_pagination_returns_domain_entities(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        repo.create(_make_ws("ws-1", "A"))
        page = repo.list_page(PageRequest(page=1, page_size=10))
        for ws in page.items:
            assert isinstance(ws, Workspace)


# ======================================================================
# Repr
# ======================================================================


class TestRepr:
    """Tests for string representations."""

    def test_repr(self, repo: SqliteWorkspaceRepositoryImpl) -> None:
        assert "SqliteWorkspaceRepositoryImpl" in repr(repo)
