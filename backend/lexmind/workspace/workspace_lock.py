"""Workspace locking interface and single-process implementation."""

import threading
from typing import Protocol, runtime_checkable


@runtime_checkable
class WorkspaceLock(Protocol):
    """Protocol for workspace-level locking.

    Implementations may provide single-process, multi-process,
    or distributed locking strategies.
    """

    def acquire(self, workspace_id: str, timeout: float = -1) -> bool:
        """Attempt to acquire a lock for *workspace_id*.

        Returns True on success, False on timeout.
        """
        ...

    def release(self, workspace_id: str) -> None:
        """Release the lock for *workspace_id*."""
        ...

    def is_locked(self, workspace_id: str) -> bool:
        """Return True if *workspace_id* is currently locked."""
        ...


class SingleProcessLock:
    """In-process lock using threading primitives.

    Suitable for single-process deployments.  Not safe across
    multiple OS processes.
    """

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}
        self._held: dict[str, str] = {}
        self._owner = threading.get_ident()
        self._guard = threading.Lock()

    def acquire(self, workspace_id: str, timeout: float = -1) -> bool:
        """Acquire an in-process lock for *workspace_id*."""
        with self._guard:
            if workspace_id not in self._locks:
                self._locks[workspace_id] = threading.Lock()

            lock = self._locks[workspace_id]

        acquired = lock.acquire(timeout=timeout if timeout > 0 else -1)
        if acquired:
            with self._guard:
                self._held[workspace_id] = str(self._owner)
        return acquired

    def release(self, workspace_id: str) -> None:
        """Release the in-process lock for *workspace_id*."""
        with self._guard:
            lock = self._locks.get(workspace_id)
            if lock is None:
                return
            self._held.pop(workspace_id, None)
        lock.release()

    def is_locked(self, workspace_id: str) -> bool:
        """Return True if *workspace_id* is currently locked."""
        with self._guard:
            return workspace_id in self._held

    def owner(self, workspace_id: str) -> str | None:
        """Return the owner identifier for *workspace_id* lock."""
        with self._guard:
            return self._held.get(workspace_id)
