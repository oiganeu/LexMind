"""Workspace registry Protocol."""

from typing import Protocol, runtime_checkable

from lexmind.workspace.workspace import Workspace


@runtime_checkable
class WorkspaceRegistry(Protocol):
    """Protocol for tracking open workspace instances.

    The registry maintains an in-memory map of workspace_id to
    Workspace, supporting multiple concurrent open workspaces.
    """

    def register(self, workspace: Workspace) -> None:
        """Register an open workspace."""
        ...

    def unregister(self, workspace_id: str) -> None:
        """Remove a workspace from the registry."""
        ...

    def get(self, workspace_id: str) -> Workspace | None:
        """Return the open workspace or None."""
        ...

    def list_open(self) -> list[Workspace]:
        """Return all currently registered open workspaces."""
        ...

    def is_registered(self, workspace_id: str) -> bool:
        """Return True if *workspace_id* is in the registry."""
        ...
