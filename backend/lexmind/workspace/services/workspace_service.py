"""Workspace Service -- high-level facade for workspace lifecycle.

Responsibilities:
    - Coordinate validation, initialization, and lifecycle operations
    - Single entry point for all workspace operations
    - Publishes WorkspaceCreated event after successful creation
    - No direct filesystem access
"""

from __future__ import annotations

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.repositories.pagination import PageRequest, PageResult
from lexmind.workspace.services.workspace_initializer import WorkspaceInitializer
from lexmind.workspace.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)
from lexmind.workspace.services.workspace_validator import WorkspaceValidator
from lexmind.workspace.workspace_events import WorkspaceCreated


class WorkspaceService:
    """High-level facade for workspace lifecycle management.

    Coordinates validation, initialization, and lifecycle operations.
    All workspace mutations go through this service.
    """

    def __init__(
        self,
        workspace_repository: object,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with repository and optional event bus.

        Args:
            workspace_repository: Used for all persistence operations.
            event_bus: Used to publish lifecycle events.
        """
        self._repo = workspace_repository
        self._validator = WorkspaceValidator(workspace_repository)
        self._initializer = WorkspaceInitializer(workspace_repository)
        self._lifecycle = WorkspaceLifecycleManager(workspace_repository, event_bus)
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        description: str = "",
        owner_id: str = "",
    ) -> Workspace:
        """Create a new workspace.

        Validates name, persists the entity, and publishes WorkspaceCreated.

        Args:
            name: Unique workspace name.
            description: Human-readable description.
            owner_id: ID of the workspace owner.

        Returns:
            The newly created Workspace.

        Raises:
            WorkspaceValidationError: If name validation fails.
        """
        self._validator.validate_all(name)
        ws = self._initializer.create_workspace(name, description, owner_id)
        self._publish(WorkspaceCreated(aggregate_id=ws.id, workspace_name=name))
        return ws

    def open(self, workspace_id: str) -> Workspace:
        """Open a workspace (set active).

        Args:
            workspace_id: ID of the workspace to open.

        Returns:
            The updated workspace.
        """
        return self._lifecycle.open(workspace_id)

    def close(self, workspace_id: str) -> Workspace:
        """Close a workspace (set inactive).

        Args:
            workspace_id: ID of the workspace to close.

        Returns:
            The updated workspace.
        """
        return self._lifecycle.close(workspace_id)

    def archive(self, workspace_id: str) -> Workspace:
        """Archive a workspace.

        Args:
            workspace_id: ID of the workspace to archive.

        Returns:
            The updated workspace.
        """
        return self._lifecycle.archive(workspace_id)

    def delete(self, workspace_id: str) -> None:
        """Permanently delete a workspace.

        Args:
            workspace_id: ID of the workspace to delete.
        """
        self._lifecycle.delete(workspace_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Retrieve a workspace by ID.  Returns None if not found."""
        return self._lifecycle.get(workspace_id)

    def get_by_name(self, name: str) -> Workspace | None:
        """Retrieve a workspace by name.  Returns None if not found."""
        return self._repo.get_by_name(name)  # type: ignore[union-attr]

    def exists(self, workspace_id: str) -> bool:
        """Return True if the workspace exists and is active."""
        return self._lifecycle.exists(workspace_id)

    def list_all(self) -> list[Workspace]:
        """Return all active workspaces."""
        return self._repo.list_all()  # type: ignore[union-attr]

    def list_page(self, page_request: PageRequest) -> PageResult[Workspace]:
        """Return a paginated list of active workspaces."""
        return self._repo.list_page(page_request)  # type: ignore[union-attr]

    def count(self) -> int:
        """Return the total number of active workspaces."""
        return self._repo.count()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def initialize_metadata(self, workspace_id: str) -> Workspace:
        """Initialize metadata for an existing workspace.

        Args:
            workspace_id: ID of the workspace.

        Returns:
            The workspace with refreshed metadata.
        """
        return self._initializer.initialize_metadata(workspace_id)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_name(self, name: str) -> None:
        """Validate a workspace name without persisting.

        Raises:
            WorkspaceValidationError: If the name is invalid.
        """
        self._validator.validate_name(name)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]
