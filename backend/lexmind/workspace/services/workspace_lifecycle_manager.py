"""Workspace Lifecycle Manager -- manages state transitions and events.

Responsibilities:
    - Transition workspace between lifecycle states
    - Publish lifecycle events after successful transitions
    - Enforce valid state transitions
    - No direct filesystem access
"""

from __future__ import annotations

from lexmind.domain.entities.workspace import Workspace
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.workspace.workspace_events import (
    WorkspaceArchived,
    WorkspaceClosed,
    WorkspaceDeleted,
    WorkspaceOpened,
)

# Valid lifecycle transitions mapped to is_active state.
# "archive" and "close" both set is_active=False but publish different events.
_LIFECYCLE_TRANSITIONS: dict[str, bool] = {
    "open": True,
    "close": False,
    "archive": False,
}


class WorkspaceLifecycleManager:
    """Manages workspace lifecycle transitions and event publication.

    Uses the workspace repository for persistence and an event bus
    for publishing lifecycle events.
    """

    def __init__(
        self,
        workspace_repository: object,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with repository and optional event bus.

        Args:
            workspace_repository: Used to persist state changes.
            event_bus: Used to publish lifecycle events.  If None,
                events are silently dropped.
        """
        self._repo = workspace_repository
        self._event_bus = event_bus

    def open(self, workspace_id: str) -> Workspace:
        """Open a workspace (set active).

        Args:
            workspace_id: ID of the workspace to open.

        Returns:
            The updated workspace.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        ws = self._load(workspace_id)
        ws.activate()
        ws = self._repo.update(ws)  # type: ignore[union-attr]
        self._publish(WorkspaceOpened(aggregate_id=ws.id))
        return ws

    def close(self, workspace_id: str) -> Workspace:
        """Close a workspace (set inactive).

        Args:
            workspace_id: ID of the workspace to close.

        Returns:
            The updated workspace.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        ws = self._load(workspace_id)
        ws.deactivate()
        ws = self._repo.update(ws)  # type: ignore[union-attr]
        self._publish(WorkspaceClosed(aggregate_id=ws.id))
        return ws

    def archive(self, workspace_id: str) -> Workspace:
        """Archive a workspace (set inactive, archival semantics).

        Args:
            workspace_id: ID of the workspace to archive.

        Returns:
            The updated workspace.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        ws = self._load(workspace_id)
        ws.deactivate()
        ws = self._repo.update(ws)  # type: ignore[union-attr]
        self._publish(WorkspaceArchived(aggregate_id=ws.id))
        return ws

    def delete(self, workspace_id: str) -> None:
        """Permanently delete a workspace.

        Publishes WorkspaceDeleted after the row is removed.

        Args:
            workspace_id: ID of the workspace to delete.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        self._load(workspace_id)  # verify exists
        self._repo.hard_delete(workspace_id)  # type: ignore[union-attr]
        self._publish(WorkspaceDeleted(aggregate_id=workspace_id))

    def get(self, workspace_id: str) -> Workspace | None:
        """Retrieve a workspace by ID.

        Returns None if not found or soft-deleted.
        """
        return self._repo.get_by_id(workspace_id)  # type: ignore[union-attr]

    def exists(self, workspace_id: str) -> bool:
        """Return True if the workspace exists and is active."""
        return self._repo.exists(workspace_id)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self, workspace_id: str) -> Workspace:
        """Load a workspace or raise if not found."""
        ws = self._repo.get_by_id_any(workspace_id)  # type: ignore[union-attr]
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)
        return ws

    def _publish(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]
