"""Tests for Workspace Lifecycle Services (TASK-0020).

Covers:
    - WorkspaceValidator: name validation, uniqueness checks
    - WorkspaceInitializer: create, initialize metadata
    - WorkspaceLifecycleManager: open, close, archive, delete, events
    - WorkspaceService: full lifecycle facade
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.repositories.pagination import PageRequest
from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.session import SessionManager
from lexmind.repositories.workspace_repository import (
    SqliteWorkspaceRepositoryImpl,
)
from lexmind.workspace.services.workspace_initializer import (
    WorkspaceInitializer,
)
from lexmind.workspace.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)
from lexmind.workspace.services.workspace_service import WorkspaceService
from lexmind.workspace.services.workspace_validator import (
    WorkspaceValidator,
)
from lexmind.workspace.workspace_events import (
    WorkspaceArchived,
    WorkspaceClosed,
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceOpened,
)
from lexmind.workspace.workspace_exceptions import (
    WorkspaceValidationError,
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
def repo(
    session_mgr: SessionManager,
) -> SqliteWorkspaceRepositoryImpl:
    """Provide a WorkspaceRepository."""
    return SqliteWorkspaceRepositoryImpl(session_mgr)


@pytest.fixture()
def event_bus() -> MagicMock:
    """Provide a mock event bus."""
    return MagicMock()


@pytest.fixture()
def validator(
    repo: SqliteWorkspaceRepositoryImpl,
) -> WorkspaceValidator:
    """Provide a WorkspaceValidator."""
    return WorkspaceValidator(repo)


@pytest.fixture()
def initializer(
    repo: SqliteWorkspaceRepositoryImpl,
) -> WorkspaceInitializer:
    """Provide a WorkspaceInitializer."""
    return WorkspaceInitializer(repo)


@pytest.fixture()
def lifecycle(
    repo: SqliteWorkspaceRepositoryImpl,
    event_bus: MagicMock,
) -> WorkspaceLifecycleManager:
    """Provide a WorkspaceLifecycleManager."""
    return WorkspaceLifecycleManager(repo, event_bus)


@pytest.fixture()
def service(
    repo: SqliteWorkspaceRepositoryImpl,
    event_bus: MagicMock,
) -> WorkspaceService:
    """Provide a WorkspaceService."""
    return WorkspaceService(repo, event_bus)


def _create_ws(
    repo: SqliteWorkspaceRepositoryImpl,
    ws_id: str = "ws-1",
    name: str = "Test Workspace",
) -> Workspace:
    """Helper: create and persist a workspace directly."""
    ws = Workspace(id=ws_id, name=name, is_active=True)
    return repo.create(ws)


# ===================================================================
# WorkspaceValidator
# ===================================================================


class TestValidator:
    """Tests for WorkspaceValidator."""

    def test_valid_name_passes(
        self, validator: WorkspaceValidator
    ) -> None:
        """A well-formed name should not raise."""
        validator.validate_name("My Workspace")

    def test_empty_name_raises(
        self, validator: WorkspaceValidator
    ) -> None:
        """An empty name should raise WorkspaceValidationError."""
        with pytest.raises(WorkspaceValidationError, match="empty"):
            validator.validate_name("")

    def test_whitespace_only_raises(
        self, validator: WorkspaceValidator
    ) -> None:
        """A whitespace-only name should raise."""
        with pytest.raises(WorkspaceValidationError, match="empty"):
            validator.validate_name("   ")

    def test_too_long_raises(
        self, validator: WorkspaceValidator
    ) -> None:
        """A name exceeding 255 chars should raise."""
        with pytest.raises(WorkspaceValidationError, match="exceed"):
            validator.validate_name("a" * 256)

    def test_invalid_characters_raises(
        self, validator: WorkspaceValidator
    ) -> None:
        """Names with special characters should raise."""
        with pytest.raises(WorkspaceValidationError, match="contain"):
            validator.validate_name("workspace@#$!")

    def test_valid_characters_pass(
        self, validator: WorkspaceValidator
    ) -> None:
        """Names with letters, digits, hyphens, underscores pass."""
        validator.validate_name("workspace-1_test v2")

    def test_uniqueness_check_fails(
        self, repo: SqliteWorkspaceRepositoryImpl
    ) -> None:
        """Duplicate name should raise WorkspaceValidationError."""
        _create_ws(repo, ws_id="ws-1", name="Taken")
        v = WorkspaceValidator(repo)
        with pytest.raises(
            WorkspaceValidationError, match="already exists"
        ):
            v.validate_uniqueness("Taken")

    def test_uniqueness_check_passes(
        self, repo: SqliteWorkspaceRepositoryImpl
    ) -> None:
        """Unique name should not raise."""
        v = WorkspaceValidator(repo)
        v.validate_uniqueness("Unique Name")

    def test_validate_all_combines(
        self, repo: SqliteWorkspaceRepositoryImpl
    ) -> None:
        """validate_all runs both name and uniqueness checks."""
        v = WorkspaceValidator(repo)
        v.validate_all("Fresh Name")

    def test_no_repo_skips_uniqueness(self) -> None:
        """Without a repo, uniqueness check is skipped."""
        v = WorkspaceValidator(None)
        v.validate_uniqueness("Anything")


# ===================================================================
# WorkspaceInitializer
# ===================================================================


class TestInitializer:
    """Tests for WorkspaceInitializer."""

    def test_create_workspace(
        self, initializer: WorkspaceInitializer
    ) -> None:
        """create_workspace should persist and return a Workspace."""
        ws = initializer.create_workspace(
            "My WS", description="desc", owner_id="u1"
        )
        assert isinstance(ws, Workspace)
        assert ws.name == "My WS"
        assert ws.description == "desc"
        assert ws.owner_id == "u1"
        assert ws.is_active is True

    def test_create_persists_in_repo(
        self,
        initializer: WorkspaceInitializer,
        repo: SqliteWorkspaceRepositoryImpl,
    ) -> None:
        """Created workspace should be retrievable from the repo."""
        ws = initializer.create_workspace("Lookup WS")
        loaded = repo.get_by_id(ws.id)
        assert loaded is not None
        assert loaded.name == "Lookup WS"

    def test_initialize_metadata(
        self, initializer: WorkspaceInitializer
    ) -> None:
        """initialize_metadata should touch and update the workspace."""
        ws = initializer.create_workspace("To Init")
        updated = initializer.initialize_metadata(ws.id)
        assert updated.id == ws.id

    def test_initialize_metadata_not_found(
        self, initializer: WorkspaceInitializer
    ) -> None:
        """initialize_metadata should raise for non-existent."""
        with pytest.raises(EntityNotFoundError):
            initializer.initialize_metadata("does-not-exist")


# ===================================================================
# WorkspaceLifecycleManager
# ===================================================================


RepoImpl = SqliteWorkspaceRepositoryImpl


class TestLifecycleManager:
    """Tests for WorkspaceLifecycleManager."""

    def _make_ws(
        self, repo: RepoImpl, ws_id: str = "ws-lc"
    ) -> Workspace:
        """Helper: create a workspace in the repo."""
        return _create_ws(repo, ws_id=ws_id, name="Lifecycle WS")

    def test_open(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """open() should set workspace active."""
        ws = self._make_ws(repo)
        opened = lifecycle.open(ws.id)
        assert opened.is_active is True

    def test_open_publishes_event(
        self,
        lifecycle: WorkspaceLifecycleManager,
        event_bus: MagicMock,
        repo: RepoImpl,
    ) -> None:
        """open() should publish a WorkspaceOpened event."""
        ws = self._make_ws(repo)
        lifecycle.open(ws.id)
        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert isinstance(event, WorkspaceOpened)

    def test_close(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """close() should set workspace inactive."""
        ws = self._make_ws(repo)
        closed = lifecycle.close(ws.id)
        assert closed.is_active is False

    def test_close_publishes_event(
        self,
        lifecycle: WorkspaceLifecycleManager,
        event_bus: MagicMock,
        repo: RepoImpl,
    ) -> None:
        """close() should publish a WorkspaceClosed event."""
        ws = self._make_ws(repo)
        lifecycle.close(ws.id)
        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert isinstance(event, WorkspaceClosed)

    def test_archive(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """archive() should set workspace inactive."""
        ws = self._make_ws(repo)
        archived = lifecycle.archive(ws.id)
        assert archived.is_active is False

    def test_archive_publishes_event(
        self,
        lifecycle: WorkspaceLifecycleManager,
        event_bus: MagicMock,
        repo: RepoImpl,
    ) -> None:
        """archive() should publish a WorkspaceArchived event."""
        ws = self._make_ws(repo)
        lifecycle.archive(ws.id)
        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert isinstance(event, WorkspaceArchived)

    def test_delete(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """delete() should hard-delete the workspace."""
        ws = self._make_ws(repo)
        lifecycle.delete(ws.id)
        loaded = repo.get_by_id(ws.id)
        assert loaded is None

    def test_delete_publishes_event(
        self,
        lifecycle: WorkspaceLifecycleManager,
        event_bus: MagicMock,
        repo: RepoImpl,
    ) -> None:
        """delete() should publish a WorkspaceDeleted event."""
        ws = self._make_ws(repo)
        lifecycle.delete(ws.id)
        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert isinstance(event, WorkspaceDeleted)
        assert event.aggregate_id == ws.id

    def test_open_nonexistent_raises(
        self, lifecycle: WorkspaceLifecycleManager
    ) -> None:
        """Opening non-existent workspace should raise."""
        with pytest.raises(EntityNotFoundError):
            lifecycle.open("does-not-exist")

    def test_close_nonexistent_raises(
        self, lifecycle: WorkspaceLifecycleManager
    ) -> None:
        """Closing non-existent workspace should raise."""
        with pytest.raises(EntityNotFoundError):
            lifecycle.close("does-not-exist")

    def test_delete_nonexistent_raises(
        self, lifecycle: WorkspaceLifecycleManager
    ) -> None:
        """Deleting non-existent workspace should raise."""
        with pytest.raises(EntityNotFoundError):
            lifecycle.delete("does-not-exist")

    def test_get(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """get() should return the workspace."""
        ws = self._make_ws(repo)
        loaded = lifecycle.get(ws.id)
        assert loaded is not None
        assert loaded.id == ws.id

    def test_get_nonexistent_returns_none(
        self, lifecycle: WorkspaceLifecycleManager
    ) -> None:
        """get() should return None for non-existent workspace."""
        assert lifecycle.get("nope") is None

    def test_exists(
        self, lifecycle: WorkspaceLifecycleManager, repo: RepoImpl
    ) -> None:
        """exists() should return True for active workspace."""
        ws = self._make_ws(repo)
        assert lifecycle.exists(ws.id) is True

    def test_exists_deleted_returns_false(
        self,
        lifecycle: WorkspaceLifecycleManager,
        repo: RepoImpl,
    ) -> None:
        """exists() should return False after hard delete."""
        ws = self._make_ws(repo)
        lifecycle.delete(ws.id)
        assert lifecycle.exists(ws.id) is False

    def test_no_event_bus_does_not_crash(
        self, repo: RepoImpl
    ) -> None:
        """Operations should succeed even without an event bus."""
        lm = WorkspaceLifecycleManager(repo, event_bus=None)
        ws = _create_ws(repo, ws_id="ws-nb", name="No Bus")
        opened = lm.open(ws.id)
        assert opened.is_active is True

    def test_close_then_reopen(
        self,
        lifecycle: WorkspaceLifecycleManager,
        repo: RepoImpl,
    ) -> None:
        """A closed workspace can be reopened."""
        ws = self._make_ws(repo)
        lifecycle.close(ws.id)
        reopened = lifecycle.open(ws.id)
        assert reopened.is_active is True


# ===================================================================
# WorkspaceService (facade)
# ===================================================================


class TestWorkspaceService:
    """Tests for the WorkspaceService facade."""

    def test_create(self, service: WorkspaceService) -> None:
        """create() should return a new workspace."""
        ws = service.create(
            "Facade WS", description="test", owner_id="u1"
        )
        assert isinstance(ws, Workspace)
        assert ws.name == "Facade WS"
        assert ws.is_active is True

    def test_create_publishes_event(
        self, service: WorkspaceService, event_bus: MagicMock
    ) -> None:
        """create() should publish WorkspaceCreated."""
        service.create("Event WS")
        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert isinstance(event, WorkspaceCreated)
        assert event.workspace_name == "Event WS"

    def test_create_invalid_name_raises(
        self, service: WorkspaceService
    ) -> None:
        """create() with invalid name should raise."""
        with pytest.raises(WorkspaceValidationError):
            service.create("")

    def test_create_duplicate_name_raises(
        self, service: WorkspaceService
    ) -> None:
        """create() with duplicate name should raise."""
        service.create("Taken")
        with pytest.raises(
            WorkspaceValidationError, match="already exists"
        ):
            service.create("Taken")

    def test_open(self, service: WorkspaceService) -> None:
        """open() should set workspace active."""
        ws = service.create("To Open")
        opened = service.open(ws.id)
        assert opened.is_active is True

    def test_close(self, service: WorkspaceService) -> None:
        """close() should set workspace inactive."""
        ws = service.create("To Close")
        closed = service.close(ws.id)
        assert closed.is_active is False

    def test_archive(self, service: WorkspaceService) -> None:
        """archive() should set workspace inactive."""
        ws = service.create("To Archive")
        archived = service.archive(ws.id)
        assert archived.is_active is False

    def test_delete(self, service: WorkspaceService) -> None:
        """delete() should hard-delete the workspace."""
        ws = service.create("To Delete")
        service.delete(ws.id)
        assert service.get_by_id(ws.id) is None

    def test_get_by_id(self, service: WorkspaceService) -> None:
        """get_by_id() should return the workspace."""
        ws = service.create("Lookup")
        loaded = service.get_by_id(ws.id)
        assert loaded is not None
        assert loaded.name == "Lookup"

    def test_get_by_id_nonexistent(
        self, service: WorkspaceService
    ) -> None:
        """get_by_id() returns None for non-existent workspace."""
        assert service.get_by_id("nope") is None

    def test_get_by_name(self, service: WorkspaceService) -> None:
        """get_by_name() should return the workspace."""
        ws = service.create("Named WS")
        loaded = service.get_by_name("Named WS")
        assert loaded is not None
        assert loaded.id == ws.id

    def test_exists(self, service: WorkspaceService) -> None:
        """exists() should return True for active workspace."""
        ws = service.create("Exists")
        assert service.exists(ws.id) is True

    def test_list_all(self, service: WorkspaceService) -> None:
        """list_all() should return all active workspaces."""
        service.create("WS A")
        service.create("WS B")
        result = service.list_all()
        assert len(result) == 2

    def test_list_page(self, service: WorkspaceService) -> None:
        """list_page() should return paginated results."""
        for i in range(5):
            service.create(f"Page WS {i}")
        page = service.list_page(PageRequest(page=1, page_size=2))
        assert len(page.items) == 2
        assert page.total_count == 5

    def test_count(self, service: WorkspaceService) -> None:
        """count() should return total active workspaces."""
        service.create("Count A")
        service.create("Count B")
        assert service.count() == 2

    def test_initialize_metadata(
        self, service: WorkspaceService
    ) -> None:
        """initialize_metadata() should update and return."""
        ws = service.create("To Init")
        updated = service.initialize_metadata(ws.id)
        assert updated.id == ws.id

    def test_initialize_metadata_not_found(
        self, service: WorkspaceService
    ) -> None:
        """initialize_metadata() should raise for non-existent."""
        with pytest.raises(EntityNotFoundError):
            service.initialize_metadata("does-not-exist")

    def test_validate_name(self, service: WorkspaceService) -> None:
        """validate_name() should not raise for valid name."""
        service.validate_name("Good Name")

    def test_validate_name_invalid(
        self, service: WorkspaceService
    ) -> None:
        """validate_name() should raise for invalid name."""
        with pytest.raises(WorkspaceValidationError):
            service.validate_name("")

    def test_full_lifecycle(
        self, service: WorkspaceService
    ) -> None:
        """Full lifecycle: create -> open -> close -> archive -> delete."""
        ws = service.create("Lifecycle Test")
        assert ws.is_active is True

        opened = service.open(ws.id)
        assert opened.is_active is True

        closed = service.close(ws.id)
        assert closed.is_active is False

        archived = service.archive(ws.id)
        assert archived.is_active is False

        service.delete(ws.id)
        assert service.get_by_id(ws.id) is None
