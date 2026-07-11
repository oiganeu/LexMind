"""Workspace lifecycle states and transitions."""

from enum import Enum, unique


@unique
class WorkspaceStatus(Enum):
    """Lifecycle status of a workspace.

    Each workspace progresses through a defined set of states.
    Only valid transitions are permitted.
    """

    CREATED = "created"
    OPEN = "open"
    ACTIVE = "active"
    READ_ONLY = "read_only"
    LOCKED = "locked"
    CLOSED = "closed"
    ARCHIVED = "archived"
    CORRUPTED = "corrupted"


VALID_TRANSITIONS: dict[WorkspaceStatus, frozenset[WorkspaceStatus]] = {
    WorkspaceStatus.CREATED: frozenset({WorkspaceStatus.OPEN}),
    WorkspaceStatus.OPEN: frozenset({
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.READ_ONLY,
        WorkspaceStatus.CLOSED,
    }),
    WorkspaceStatus.ACTIVE: frozenset({
        WorkspaceStatus.READ_ONLY,
        WorkspaceStatus.LOCKED,
        WorkspaceStatus.CLOSED,
    }),
    WorkspaceStatus.READ_ONLY: frozenset({
        WorkspaceStatus.ACTIVE,
        WorkspaceStatus.CLOSED,
    }),
    WorkspaceStatus.LOCKED: frozenset({WorkspaceStatus.ACTIVE}),
    WorkspaceStatus.CLOSED: frozenset({
        WorkspaceStatus.ARCHIVED,
        WorkspaceStatus.OPEN,
    }),
    WorkspaceStatus.ARCHIVED: frozenset({WorkspaceStatus.OPEN}),
    WorkspaceStatus.CORRUPTED: frozenset(),
}


def can_transition(source: WorkspaceStatus, target: WorkspaceStatus) -> bool:
    """Return True if *source* -> *target* is a valid transition."""
    return target in VALID_TRANSITIONS.get(source, frozenset())
