"""Metadata store exception hierarchy."""

from lexmind.exceptions import LexMindError


class MetadataError(LexMindError):
    """Base class for metadata-store errors."""


class DatabaseError(MetadataError):
    """Raised when a database operation fails."""


class DatabaseConnectionError(DatabaseError):
    """Raised when the database connection cannot be established."""

    def __init__(self, url: str, reason: str = "") -> None:
        msg = f"Cannot connect to database: {url}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.url = url
        self.reason = reason


class SessionError(MetadataError):
    """Raised when a session operation fails."""


class SessionCommitError(SessionError):
    """Raised when a session commit fails."""

    def __init__(self, detail: str = "") -> None:
        msg = "Session commit failed"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.detail = detail


class SessionRollbackError(SessionError):
    """Raised when a session rollback fails."""

    def __init__(self, detail: str = "") -> None:
        msg = "Session rollback failed"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.detail = detail


class MigrationError(MetadataError):
    """Raised when a migration operation fails."""


class MigrationVersionError(MigrationError):
    """Raised when migration version tracking is inconsistent."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(
            f"Migration version mismatch: expected {expected}, got {actual}"
        )
        self.expected = expected
        self.actual = actual


class SchemaValidationError(MetadataError):
    """Raised when schema validation fails."""


class EntityNotFoundError(MetadataError):
    """Raised when a requested entity does not exist in the store."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConcurrencyError(MetadataError):
    """Raised when a concurrent modification is detected."""
