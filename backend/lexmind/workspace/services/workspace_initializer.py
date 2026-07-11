"""Workspace Initializer -- creates workspace entity and metadata.

Responsibilities:
    - Create a new Workspace domain entity with proper defaults
    - Persist via repository
    - Return the created entity
    - No filesystem access (delegated to StorageManager)
"""

from __future__ import annotations

from lexmind.domain.entities.workspace import Workspace
from lexmind.metadata.exceptions import EntityNotFoundError


class WorkspaceInitializer:
    """Creates and persists new workspace entities.

    Stateless service -- all methods are pure functions.
    """

    def __init__(self, workspace_repository: object) -> None:
        """Initialise with a workspace repository.

        Args:
            workspace_repository: Used to persist new workspaces.
        """
        self._repo = workspace_repository

    def create_workspace(
        self,
        name: str,
        description: str = "",
        owner_id: str = "",
    ) -> Workspace:
        """Create and persist a new workspace.

        Args:
            name: Unique workspace name.
            description: Human-readable description.
            owner_id: ID of the workspace owner.

        Returns:
            The newly created Workspace entity.
        """
        ws = Workspace(
            name=name,
            description=description,
            owner_id=owner_id,
            is_active=True,
        )
        return self._repo.create(ws)  # type: ignore[union-attr]

    def initialize_metadata(self, workspace_id: str) -> Workspace:
        """Initialize metadata fields for an existing workspace.

        Sets default counts and validates the entity is loadable.

        Args:
            workspace_id: ID of the workspace to initialize.

        Returns:
            The workspace with initialized metadata.

        Raises:
            EntityNotFoundError: If the workspace does not exist.
        """
        ws = self._repo.get_by_id(workspace_id)  # type: ignore[union-attr]
        if ws is None:
            raise EntityNotFoundError("Workspace", workspace_id)
        ws.touch()
        return self._repo.update(ws)  # type: ignore[union-attr]
