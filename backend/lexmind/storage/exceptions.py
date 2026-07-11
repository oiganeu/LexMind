"""Storage-specific exception hierarchy."""

from lexmind.exceptions import LexMindError


class StorageError(LexMindError):
    """Base class for storage-layer errors."""


class StorageNotFoundError(StorageError):
    """Raised when a requested storage object does not exist."""

    def __init__(self, uri: str) -> None:
        super().__init__(f"Storage object not found: {uri}")
        self.uri = uri


class StoragePermissionDeniedError(StorageError):
    """Raised when an operation is not permitted on the storage object."""

    def __init__(self, uri: str, operation: str = "access") -> None:
        super().__init__(f"Permission denied for '{operation}' on: {uri}")
        self.uri = uri
        self.operation = operation


class StorageAlreadyExistsError(StorageError):
    """Raised when trying to write to a path that already exists."""

    def __init__(self, uri: str) -> None:
        super().__init__(f"Storage object already exists: {uri}")
        self.uri = uri


class InvalidStorageURIError(StorageError):
    """Raised when a storage URI is malformed."""

    def __init__(self, uri: str, reason: str = "") -> None:
        msg = f"Invalid storage URI: {uri}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.uri = uri
        self.reason = reason


class StorageChecksumError(StorageError):
    """Raised when a checksum verification fails."""

    def __init__(self, uri: str, expected: str, actual: str) -> None:
        super().__init__(
            f"Checksum mismatch for '{uri}': "
            f"expected {expected}, got {actual}"
        )
        self.uri = uri
        self.expected = expected
        self.actual = actual
