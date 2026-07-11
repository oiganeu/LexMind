"""Unit of Work interface.

The Unit of Work pattern coordinates multiple repository operations
within a single transaction.  One application use case maps to
one Unit of Work which maps to one commit.

Responsibilities:
    - begin(): Start a new transaction.
    - commit(): Persist all changes.
    - rollback(): Discard all changes.
    - savepoint(): Create a nested transaction savepoint.
    - release(): Release a savepoint.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol):
    """Transaction coordinator for repository operations.

    Usage::

        async with unit_of_work() as uow:
            uow.workspaces.save(workspace)
            uow.cases.save(case)
        # Automatic commit on clean exit, rollback on exception
    """

    def begin(self) -> None:
        """Begin a new transaction."""

    def commit(self) -> None:
        """Commit all changes made in this transaction."""

    def rollback(self) -> None:
        """Roll back all changes made in this transaction."""

    def savepoint(self, name: str) -> None:
        """Create a named savepoint within the current transaction."""

    def release(self, name: str) -> None:
        """Release a named savepoint."""
