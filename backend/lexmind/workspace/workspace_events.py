"""Workspace lifecycle domain events."""

from dataclasses import dataclass, field

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkspaceCreated(DomainEvent):
    """Raised when a new workspace is created."""

    workspace_name: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceOpened(DomainEvent):
    """Raised when a workspace is opened for use."""


@dataclass(frozen=True, slots=True)
class WorkspaceClosed(DomainEvent):
    """Raised when a workspace is closed."""


@dataclass(frozen=True, slots=True)
class WorkspaceArchived(DomainEvent):
    """Raised when a workspace is archived."""


@dataclass(frozen=True, slots=True)
class WorkspaceDeleted(DomainEvent):
    """Raised when a workspace is deleted."""


@dataclass(frozen=True, slots=True)
class WorkspaceValidationFailed(DomainEvent):
    """Raised when workspace validation fails."""

    errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class WorkspaceMigrated(DomainEvent):
    """Raised when a workspace schema is migrated."""

    from_version: str = ""
    to_version: str = ""
