"""Unit tests for the SQLite Metadata Store (TASK-0017).

Covers:
    - Database initialisation and disposal
    - Session manager (context-managed sessions, rollback)
    - CRUD repositories (Workspace, Case, Document)
    - Migration framework (apply, rollback, version tracking)
    - Pydantic schema validation
    - Exception hierarchy
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import (
    DatabaseConnectionError,
    EntityNotFoundError,
    MetadataError,
    MigrationError,
    MigrationVersionError,
    SessionCommitError,
    SessionRollbackError,
)
from lexmind.metadata.migrations import Migration, MigrationRunner, MigrationTracker
from lexmind.metadata.repositories import (
    SqliteCaseRepository,
    SqliteDocumentRepository,
    SqliteWorkspaceRepository,
)
from lexmind.metadata.schema import (
    CaseCreate,
    DocumentCreate,
    WorkspaceCreate,
    WorkspaceRead,
)
from lexmind.metadata.session import SessionManager

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
    """Provide a SessionManager over the in-memory DB."""
    return SessionManager(db.engine)


@pytest.fixture()
def ws_repo(session_mgr: SessionManager) -> SqliteWorkspaceRepository:
    """Provide a WorkspaceRepository."""
    return SqliteWorkspaceRepository(session_mgr)


@pytest.fixture()
def case_repo(session_mgr: SessionManager) -> SqliteCaseRepository:
    """Provide a CaseRepository."""
    return SqliteCaseRepository(session_mgr)


@pytest.fixture()
def doc_repo(session_mgr: SessionManager) -> SqliteDocumentRepository:
    """Provide a DocumentRepository."""
    return SqliteDocumentRepository(session_mgr)


# ======================================================================
# Helpers
# ======================================================================


def _make_workspace(
    ws_id: str = "ws-1",
    name: str = "Test Workspace",
    owner_id: str = "user-1",
) -> object:
    """Create a domain Workspace entity."""
    from lexmind.domain.entities.workspace import Workspace

    return Workspace(id=ws_id, name=name, owner_id=owner_id)


def _make_case(
    case_id: str = "case-1",
    workspace_id: str = "ws-1",
    title: str = "Test Case",
) -> object:
    """Create a domain Case entity."""
    from lexmind.domain.entities.case import Case

    return Case(id=case_id, workspace_id=workspace_id, title=title)


def _make_document(
    doc_id: str = "doc-1",
    workspace_id: str = "ws-1",
    title: str = "Test Doc",
) -> object:
    """Create a domain Document entity."""
    from lexmind.domain.entities.document import Document

    return Document(id=doc_id, workspace_id=workspace_id, title=title)


# ======================================================================
# Database
# ======================================================================


class TestDatabase:
    """Tests for Database initialisation."""

    def test_init_url(self) -> None:
        db = Database("sqlite:///test.db")
        assert db.url == "sqlite:///test.db"

    def test_initialize_creates_engine(self, db: Database) -> None:
        assert db.engine is not None

    def test_engine_before_init_raises(self) -> None:
        db = Database()
        with pytest.raises(DatabaseConnectionError):
            _ = db.engine

    def test_dispose(self) -> None:
        db = Database("sqlite:///:memory:")
        db.initialize()
        db.dispose()
        with pytest.raises(DatabaseConnectionError):
            _ = db.engine

    def test_repr(self) -> None:
        db = Database("sqlite:///x.db")
        assert "sqlite:///x.db" in repr(db)


# ======================================================================
# Session Manager
# ======================================================================


class TestSessionManager:
    """Tests for SessionManager."""

    def test_session_scope_commit(self, session_mgr: SessionManager) -> None:
        from lexmind.metadata.models import WorkspaceRow

        with session_mgr.session_scope() as session:
            session.add(WorkspaceRow(id="ws-1", name="Committed"))
        # Verify it persists
        with session_mgr.session_scope() as session:
            row = session.get(WorkspaceRow, "ws-1")
            assert row is not None
            assert row.name == "Committed"

    def test_session_scope_rollback(self, session_mgr: SessionManager) -> None:
        from sqlalchemy.exc import IntegrityError

        from lexmind.metadata.models import WorkspaceRow

        with session_mgr.session_scope() as session:
            session.add(WorkspaceRow(id="ws-1", name="OK"))
        # Duplicate name should fail and rollback
        with pytest.raises(IntegrityError), session_mgr.session_scope() as session:
            session.add(WorkspaceRow(id="ws-2", name="OK"))
        # Original row still exists
        with session_mgr.session_scope() as session:
            row = session.get(WorkspaceRow, "ws-1")
            assert row is not None

    def test_create_session(self, session_mgr: SessionManager) -> None:
        session = session_mgr.create_session()
        assert session is not None
        session.close()

    def test_repr(self, session_mgr: SessionManager) -> None:
        assert "SessionManager" in repr(session_mgr)


# ======================================================================
# Workspace Repository
# ======================================================================


class TestWorkspaceRepository:
    """Tests for SqliteWorkspaceRepository CRUD."""

    def test_create_and_get(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace()
        ws_repo.create(ws)
        loaded = ws_repo.get(ws.id)
        assert loaded is not None
        assert loaded.name == "Test Workspace"

    def test_get_not_found(self, ws_repo: SqliteWorkspaceRepository) -> None:
        assert ws_repo.get("nonexistent") is None

    def test_update(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace()
        ws_repo.create(ws)
        ws.description = "Updated description"
        ws_repo.update(ws)
        loaded = ws_repo.get(ws.id)
        assert loaded.description == "Updated description"

    def test_update_not_found(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace(ws_id="ghost")
        with pytest.raises(EntityNotFoundError):
            ws_repo.update(ws)

    def test_delete(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace()
        ws_repo.create(ws)
        ws_repo.delete(ws.id)
        assert ws_repo.get(ws.id) is None

    def test_delete_not_found(self, ws_repo: SqliteWorkspaceRepository) -> None:
        with pytest.raises(EntityNotFoundError):
            ws_repo.delete("nonexistent")

    def test_exists(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace()
        ws_repo.create(ws)
        assert ws_repo.exists(ws.id)
        assert not ws_repo.exists("nonexistent")

    def test_list_all(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws_repo.create(_make_workspace("ws-1", "A"))
        ws_repo.create(_make_workspace("ws-2", "B"))
        all_ws = ws_repo.list_all()
        assert len(all_ws) == 2

    def test_count(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws_repo.create(_make_workspace("ws-1", "A"))
        ws_repo.create(_make_workspace("ws-2", "B"))
        assert ws_repo.count() == 2

    def test_find_by_name(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace(name="Unique Name")
        ws_repo.create(ws)
        found = ws_repo.find_by_name("Unique Name")
        assert found is not None
        assert ws_repo.find_by_name("Nope") is None

    def test_find_by_owner(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws_repo.create(_make_workspace("ws-1", "A", owner_id="u1"))
        ws_repo.create(_make_workspace("ws-2", "B", owner_id="u2"))
        results = ws_repo.find_by_owner("u1")
        assert len(results) == 1

    def test_list_page(self, ws_repo: SqliteWorkspaceRepository) -> None:
        for i in range(5):
            ws_repo.create(_make_workspace(f"ws-{i}", f"W{i}"))
        from lexmind.domain.repositories.pagination import PageRequest

        page = ws_repo.list_page(PageRequest(page=1, page_size=2))
        assert len(page.items) == 2
        assert page.total_count == 5

    def test_create_persists_attributes(self, ws_repo: SqliteWorkspaceRepository) -> None:
        ws = _make_workspace()
        ws.description = "A description"
        ws.is_active = True
        ws_repo.create(ws)
        loaded = ws_repo.get(ws.id)
        assert loaded.description == "A description"
        assert loaded.is_active is True
        assert loaded.owner_id == "user-1"


# ======================================================================
# Case Repository
# ======================================================================


class TestCaseRepository:
    """Tests for SqliteCaseRepository CRUD."""

    def test_create_and_get(self, case_repo: SqliteCaseRepository) -> None:
        case = _make_case()
        case_repo.create(case)
        loaded = case_repo.get(case.id)
        assert loaded is not None
        assert loaded.title == "Test Case"

    def test_get_not_found(self, case_repo: SqliteCaseRepository) -> None:
        assert case_repo.get("nonexistent") is None

    def test_update(self, case_repo: SqliteCaseRepository) -> None:
        case = _make_case()
        case_repo.create(case)
        case.title = "Updated Title"
        case_repo.update(case)
        loaded = case_repo.get(case.id)
        assert loaded.title == "Updated Title"

    def test_delete(self, case_repo: SqliteCaseRepository) -> None:
        case = _make_case()
        case_repo.create(case)
        case_repo.delete(case.id)
        assert case_repo.get(case.id) is None

    def test_exists(self, case_repo: SqliteCaseRepository) -> None:
        case = _make_case()
        case_repo.create(case)
        assert case_repo.exists(case.id)
        assert not case_repo.exists("nonexistent")

    def test_find_by_workspace(self, case_repo: SqliteCaseRepository) -> None:
        case_repo.create(_make_case("c-1", "ws-1", "Case A"))
        case_repo.create(_make_case("c-2", "ws-2", "Case B"))
        results = case_repo.find_by_workspace("ws-1")
        assert len(results) == 1

    def test_find_by_status(self, case_repo: SqliteCaseRepository) -> None:
        from lexmind.domain.enums.domain_enums import CaseStatus

        case_repo.create(_make_case("c-1", "ws-1"))
        results = case_repo.find_by_status(CaseStatus.OPEN)
        assert len(results) == 1

    def test_find_by_title(self, case_repo: SqliteCaseRepository) -> None:
        case_repo.create(_make_case("c-1", "ws-1", "Unique Title"))
        found = case_repo.find_by_title("ws-1", "Unique Title")
        assert found is not None
        assert case_repo.find_by_title("ws-1", "Nope") is None

    def test_list_all(self, case_repo: SqliteCaseRepository) -> None:
        case_repo.create(_make_case("c-1"))
        case_repo.create(_make_case("c-2"))
        assert len(case_repo.list_all()) == 2

    def test_count(self, case_repo: SqliteCaseRepository) -> None:
        case_repo.create(_make_case("c-1"))
        assert case_repo.count() == 1

    def test_document_ids_persisted(self, case_repo: SqliteCaseRepository) -> None:
        case = _make_case()
        case.add_document("doc-1")
        case.add_document("doc-2")
        case_repo.create(case)
        loaded = case_repo.get(case.id)
        assert "doc-1" in loaded.document_ids
        assert "doc-2" in loaded.document_ids


# ======================================================================
# Document Repository
# ======================================================================


class TestDocumentRepository:
    """Tests for SqliteDocumentRepository CRUD."""

    def test_create_and_get(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc_repo.create(doc)
        loaded = doc_repo.get(doc.id)
        assert loaded is not None
        assert loaded.title == "Test Doc"

    def test_get_not_found(self, doc_repo: SqliteDocumentRepository) -> None:
        assert doc_repo.get("nonexistent") is None

    def test_update(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc_repo.create(doc)
        doc.title = "Updated Doc"
        doc_repo.update(doc)
        loaded = doc_repo.get(doc.id)
        assert loaded.title == "Updated Doc"

    def test_delete(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc_repo.create(doc)
        doc_repo.delete(doc.id)
        assert doc_repo.get(doc.id) is None

    def test_exists(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc_repo.create(doc)
        assert doc_repo.exists(doc.id)
        assert not doc_repo.exists("nonexistent")

    def test_find_by_workspace(self, doc_repo: SqliteDocumentRepository) -> None:
        doc_repo.create(_make_document("d-1", "ws-1"))
        doc_repo.create(_make_document("d-2", "ws-2"))
        results = doc_repo.find_by_workspace("ws-1")
        assert len(results) == 1

    def test_find_by_case(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document("d-1")
        doc.link_to_case("case-1")
        doc_repo.create(doc)
        doc_repo.create(_make_document("d-2", title="Other"))
        results = doc_repo.find_by_case("case-1")
        assert len(results) == 1

    def test_find_by_hash(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        from lexmind.domain.value_objects.file import FileHash

        doc.file_hash = FileHash(value="a" * 40)
        doc_repo.create(doc)
        found = doc_repo.find_by_hash("a" * 40)
        assert found is not None
        assert doc_repo.find_by_hash("b" * 40) is None

    def test_find_by_status(self, doc_repo: SqliteDocumentRepository) -> None:
        from lexmind.domain.enums.domain_enums import DocumentStatus

        doc_repo.create(_make_document("d-1"))
        results = doc_repo.find_by_status("ws-1", DocumentStatus.DRAFT)
        assert len(results) == 1

    def test_find_duplicates(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document("d-1")
        doc.is_duplicate = True
        doc_repo.create(doc)
        doc_repo.create(_make_document("d-2"))
        results = doc_repo.find_duplicates("ws-1")
        assert len(results) == 1

    def test_list_all(self, doc_repo: SqliteDocumentRepository) -> None:
        doc_repo.create(_make_document("d-1"))
        doc_repo.create(_make_document("d-2"))
        assert len(doc_repo.list_all()) == 2

    def test_count(self, doc_repo: SqliteDocumentRepository) -> None:
        doc_repo.create(_make_document("d-1"))
        assert doc_repo.count() == 1

    def test_tags_persisted(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc.add_tag("important")
        doc.add_tag("legal")
        doc_repo.create(doc)
        loaded = doc_repo.get(doc.id)
        assert "important" in loaded.tag_names
        assert "legal" in loaded.tag_names

    def test_case_ids_persisted(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document()
        doc.link_to_case("case-1")
        doc.link_to_case("case-2")
        doc_repo.create(doc)
        loaded = doc_repo.get(doc.id)
        assert "case-1" in loaded.case_ids
        assert "case-2" in loaded.case_ids

    def test_update_not_found(self, doc_repo: SqliteDocumentRepository) -> None:
        doc = _make_document(doc_id="ghost")
        with pytest.raises(EntityNotFoundError):
            doc_repo.update(doc)


# ======================================================================
# Migrations
# ======================================================================


class TestMigrationTracker:
    """Tests for MigrationTracker."""

    def test_applied_versions_empty(self, db: Database) -> None:
        tracker = MigrationTracker(db.engine)
        assert tracker.applied_versions() == []

    def test_record_and_check(self, db: Database) -> None:
        tracker = MigrationTracker(db.engine)
        tracker.record_applied("001", "init")
        assert tracker.is_applied("001")
        assert not tracker.is_applied("002")

    def test_remove_record(self, db: Database) -> None:
        tracker = MigrationTracker(db.engine)
        tracker.record_applied("001")
        tracker.remove_record("001")
        assert not tracker.is_applied("001")


class TestMigrationRunner:
    """Tests for MigrationRunner."""

    def test_migrate_up(self, db: Database) -> None:
        applied_tables: list[str] = []

        def up(engine: object) -> None:
            from sqlalchemy import text

            with engine.connect() as conn:  # type: ignore[union-attr]
                conn.execute(text("CREATE TABLE t1 (id INTEGER PRIMARY KEY)"))
                conn.commit()
            applied_tables.append("t1")

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", description="create t1", up=up))
        result = runner.migrate_up()
        assert result == ["001"]
        assert "t1" in applied_tables

    def test_pending(self, db: Database) -> None:
        def noop(engine: object) -> None:
            pass

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=noop))
        runner.add(Migration(version="002", up=noop))
        assert len(runner.pending()) == 2
        runner.migrate_up()
        assert len(runner.pending()) == 0

    def test_current_version(self, db: Database) -> None:
        def noop(engine: object) -> None:
            pass

        runner = MigrationRunner(db.engine)
        assert runner.current_version() is None
        runner.add(Migration(version="001", up=noop))
        runner.migrate_up()
        assert runner.current_version() == "001"

    def test_migrate_up_failure(self, db: Database) -> None:
        def bad(engine: object) -> None:
            raise RuntimeError("boom")

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=bad))
        with pytest.raises(MigrationError, match="001"):
            runner.migrate_up()

    def test_migrate_down(self, db: Database) -> None:
        def noop(engine: object) -> None:
            pass

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=noop, down=noop))
        runner.add(Migration(version="002", up=noop, down=noop))
        runner.migrate_up()
        rolled = runner.migrate_down("001")
        assert "002" in rolled
        assert "001" in rolled
        assert runner.current_version() is None

    def test_migrate_down_not_applied(self, db: Database) -> None:
        def noop(engine: object) -> None:
            pass

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=noop))
        with pytest.raises(MigrationVersionError):
            runner.migrate_down("001")

    def test_migrate_down_no_rollback(self, db: Database) -> None:
        def noop(engine: object) -> None:
            pass

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=noop, down=None))
        runner.migrate_up()
        with pytest.raises(MigrationError, match="no rollback"):
            runner.migrate_down("001")

    def test_idempotent_migrate_up(self, db: Database) -> None:
        call_count = 0

        def counter(engine: object) -> None:
            nonlocal call_count
            call_count += 1

        runner = MigrationRunner(db.engine)
        runner.add(Migration(version="001", up=counter))
        runner.migrate_up()
        runner.migrate_up()  # should be no-op
        assert call_count == 1


# ======================================================================
# Pydantic Schemas
# ======================================================================


class TestSchemas:
    """Tests for Pydantic validation schemas."""

    def test_workspace_create_valid(self) -> None:
        schema = WorkspaceCreate(name="Test")
        assert schema.name == "Test"

    def test_workspace_create_empty_name_fails(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            WorkspaceCreate(name="")

    def test_case_create_valid(self) -> None:
        schema = CaseCreate(workspace_id="ws-1", title="Case")
        assert schema.workspace_id == "ws-1"

    def test_case_create_empty_title_fails(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CaseCreate(workspace_id="ws-1", title="")

    def test_document_create_valid(self) -> None:
        schema = DocumentCreate(workspace_id="ws-1")
        assert schema.workspace_id == "ws-1"

    def test_document_create_empty_workspace_fails(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DocumentCreate(workspace_id="")

    def test_workspace_read_from_attributes(self) -> None:

        ws = WorkspaceRead(
            id="ws-1",
            name="Test",
            description="",
            owner_id="u1",
            is_active=True,
            document_count=0,
            case_count=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert ws.id == "ws-1"


# ======================================================================
# Exceptions
# ======================================================================


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_metadata_error_is_lexmind_error(self) -> None:
        from lexmind.exceptions import LexMindError

        assert issubclass(MetadataError, LexMindError)

    def test_database_connection_error(self) -> None:
        exc = DatabaseConnectionError("sqlite:///x.db", "timeout")
        assert "timeout" in str(exc)
        assert exc.url == "sqlite:///x.db"

    def test_entity_not_found(self) -> None:
        exc = EntityNotFoundError("Workspace", "ws-1")
        assert "Workspace" in str(exc)
        assert exc.entity_id == "ws-1"

    def test_session_commit_error(self) -> None:
        exc = SessionCommitError("detail")
        assert exc.detail == "detail"

    def test_session_rollback_error(self) -> None:
        exc = SessionRollbackError("boom")
        assert exc.detail == "boom"

    def test_migration_version_error(self) -> None:
        exc = MigrationVersionError("002", "001")
        assert exc.expected == "002"
        assert exc.actual == "001"


# ======================================================================
# No Infrastructure Dependencies in Domain
# ======================================================================


class TestNoInfrastructureDependencies:
    """Ensure domain layer has no SQLAlchemy imports."""

    def test_no_sqlalchemy_in_domain(self) -> None:
        import ast
        from pathlib import Path

        pkg_dir = Path(__file__).resolve().parent.parent / "lexmind" / "domain"
        for py_file in pkg_dir.rglob("*.py"):
            content = py_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = node.module or ""
                    assert "sqlalchemy" not in mod.lower(), (
                        f"{py_file.name} imports SQLAlchemy: {mod}"
                    )
