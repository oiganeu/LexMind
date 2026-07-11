"""Repository error model.

All repository errors inherit from ``RepositoryError``.
Infrastructure implementations raise these when persistence
operations fail.  No infrastructure-specific exceptions leak
through these contracts.
"""

from lexmind.exceptions import LexMindError


class RepositoryError(LexMindError):
    """Base class for all repository-layer errors."""


class ConcurrencyError(RepositoryError):
    """Raised when an optimistic concurrency conflict is detected.

    This happens when an entity was modified by another process
    between the time it was read and the time the update is attempted.
    """

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"Concurrency conflict on {entity_type} '{entity_id}'"
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class EntityNotFoundError(RepositoryError):
    """Raised when a requested entity does not exist in the repository."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(f"{entity_type} '{identifier}' already exists")
        self.entity_type = entity_type
        self.identifier = identifier


class TransactionError(RepositoryError):
    """Raised when a transaction operation fails."""

    def __init__(self, operation: str, reason: str = "") -> None:
        msg = f"Transaction operation '{operation}' failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.operation = operation
