"""Workspace loader Protocol."""

from typing import Protocol, runtime_checkable

from lexmind.workspace.workspace import Workspace


@runtime_checkable
class WorkspaceLoader(Protocol):
    """Protocol for loading an existing workspace from storage.

    Implementations read the manifest, validate the directory
    structure, and return a fully hydrated Workspace instance.
    """

    def load(self, workspace_id: str) -> Workspace:
        """Load a workspace by its identifier.

        Raises WorkspaceNotFoundError if the workspace does not exist.
        Raises WorkspaceCorruptedError if data is inconsistent.
        """
        ...

    def load_from_path(self, path: str) -> Workspace:
        """Load a workspace from an explicit filesystem path."""
        ...

    def exists(self, workspace_id: str) -> bool:
        """Return True if a workspace with *workspace_id* can be loaded."""
        ...
