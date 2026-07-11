"""Workspace repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class WorkspaceRepository(BaseRepository[Workspace], Protocol):
    """Persistence contract for Workspace aggregates.

    Extends BaseRepository with workspace-specific queries.
    """

    def find_by_name(self, name: str) -> Workspace | None:
        """Find a workspace by its exact name."""

    def find_by_owner(self, owner_id: str) -> list[Workspace]:
        """Find all workspaces owned by a user."""
