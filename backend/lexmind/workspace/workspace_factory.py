"""Workspace factory Protocol."""

from typing import Protocol, runtime_checkable

from lexmind.workspace.workspace import Workspace


@runtime_checkable
class WorkspaceFactory(Protocol):
    """Protocol for creating new workspace instances.

    Implementations handle initial directory scaffolding,
    manifest creation, and default configuration.
    """

    def create(
        self,
        name: str,
        description: str = "",
        owner_id: str = "",
        language: str = "ro",
        jurisdiction: str = "",
    ) -> Workspace:
        """Create and return a new workspace in CREATED state."""
        ...

    def create_with_manifest(
        self,
        name: str,
        manifest_version: str = "1.0.0",
        description: str = "",
        owner_id: str = "",
    ) -> Workspace:
        """Create a workspace with an explicit manifest version."""
        ...
