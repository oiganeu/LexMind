"""Lifecycle state machine for LexMind modules."""

from enum import StrEnum


class LifecycleState(StrEnum):
    """Enumeration of module lifecycle states."""

    CREATED = "created"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    STARTED = "started"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"

    def is_terminal(self) -> bool:
        """Return True for non-recoverable states."""
        return self in {LifecycleState.STOPPED, LifecycleState.FAILED}
