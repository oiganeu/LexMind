"""Workspace manager -- lifecycle orchestrator.

Coordinates creation, opening, closing, locking, and migration
of workspaces by delegating to registered collaborators.
"""

from lexmind.workspace.workspace import Workspace
from lexmind.workspace.workspace_events import (
    WorkspaceArchived,
    WorkspaceClosed,
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceMigrated,
    WorkspaceOpened,
    WorkspaceValidationFailed,
)
from lexmind.workspace.workspace_exceptions import (
    WorkspaceAlreadyOpenError,
    WorkspaceLockError,
    WorkspaceNotFoundError,
)
from lexmind.workspace.workspace_factory import WorkspaceFactory
from lexmind.workspace.workspace_loader import WorkspaceLoader
from lexmind.workspace.workspace_lock import WorkspaceLock
from lexmind.workspace.workspace_registry import WorkspaceRegistry


class WorkspaceManager:
    """Orchestrates workspace lifecycle operations.

    Delegates persistence to :class:`WorkspaceFactory`,
    :class:`WorkspaceLoader`, and :class:`WorkspaceRegistry`.
    Publishes events via the optional *event_bus*.
    """

    def __init__(
        self,
        factory: WorkspaceFactory,
        loader: WorkspaceLoader,
        registry: WorkspaceRegistry,
        lock: WorkspaceLock | None = None,
        event_bus: object | None = None,
    ) -> None:
        self._factory = factory
        self._loader = loader
        self._registry = registry
        self._lock = lock
        self._event_bus = event_bus

    def _publish(self, event: object) -> None:
        if self._event_bus is not None and hasattr(self._event_bus, "publish"):
            self._event_bus.publish(event)

    def create_workspace(
        self,
        name: str,
        description: str = "",
        owner_id: str = "",
        language: str = "ro",
        jurisdiction: str = "",
    ) -> Workspace:
        """Create, register, and return a new workspace."""
        ws = self._factory.create(
            name=name,
            description=description,
            owner_id=owner_id,
            language=language,
            jurisdiction=jurisdiction,
        )
        self._registry.register(ws)
        self._publish(WorkspaceCreated(
            aggregate_id=ws.id,
            workspace_name=ws.name,
        ))
        return ws

    def open_workspace(self, workspace_id: str) -> Workspace:
        """Open an existing workspace by loading and registering it."""
        if self._registry.is_registered(workspace_id):
            raise WorkspaceAlreadyOpenError(workspace_id)

        if self._lock is not None and not self._lock.acquire(workspace_id):
            raise WorkspaceLockError(workspace_id, "could not acquire lock")

        ws = self._loader.load(workspace_id)
        ws.open()
        self._registry.register(ws)
        self._publish(WorkspaceOpened(aggregate_id=ws.id))
        return ws

    def close_workspace(self, workspace_id: str) -> None:
        """Close an open workspace and release its lock."""
        ws = self._registry.get(workspace_id)
        if ws is None:
            raise WorkspaceNotFoundError(workspace_id)

        ws.close()
        self._registry.unregister(workspace_id)
        if self._lock is not None:
            self._lock.release(workspace_id)
        self._publish(WorkspaceClosed(aggregate_id=ws.id))

    def archive_workspace(self, workspace_id: str) -> None:
        """Archive a closed workspace."""
        ws = self._registry.get(workspace_id)
        if ws is None:
            raise WorkspaceNotFoundError(workspace_id)

        ws.archive()
        self._registry.unregister(workspace_id)
        if self._lock is not None:
            self._lock.release(workspace_id)
        self._publish(WorkspaceArchived(aggregate_id=ws.id))

    def delete_workspace(self, workspace_id: str) -> None:
        """Delete a workspace (must be closed first)."""
        ws = self._registry.get(workspace_id)
        if ws is not None:
            self._registry.unregister(workspace_id)
            if self._lock is not None:
                self._lock.release(workspace_id)
        self._publish(WorkspaceDeleted(aggregate_id=workspace_id))

    def validate_workspace(self, workspace_id: str) -> tuple[str, ...]:
        """Validate a workspace and return any errors found."""
        ws = self._registry.get(workspace_id)
        if ws is None:
            raise WorkspaceNotFoundError(workspace_id)

        result = ws.validate_manifest()
        if not result.is_valid:
            self._publish(WorkspaceValidationFailed(
                aggregate_id=ws.id,
                errors=result.errors,
            ))
        return result.errors

    def migrate_workspace(self, workspace_id: str, to_version: str) -> None:
        """Migrate a workspace to a new manifest version."""
        ws = self._registry.get(workspace_id)
        if ws is None:
            raise WorkspaceNotFoundError(workspace_id)

        from_version = ws.version
        ws.version = to_version
        self._publish(WorkspaceMigrated(
            aggregate_id=ws.id,
            from_version=from_version,
            to_version=to_version,
        ))

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        """Return the open workspace or None."""
        return self._registry.get(workspace_id)

    def list_open(self) -> list[Workspace]:
        """Return all currently open workspaces."""
        return self._registry.list_open()
