"""Workspace metadata value object."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class WorkspaceMetadata:
    """Immutable metadata describing a workspace.

    This value object captures all descriptive information about
    a workspace that does not affect its operational state.
    """

    workspace_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: str = "1.0.0"
    owner_id: str = ""
    tags: tuple[str, ...] = ()
    language: str = "ro"
    jurisdiction: str = ""
    status: str = "created"
