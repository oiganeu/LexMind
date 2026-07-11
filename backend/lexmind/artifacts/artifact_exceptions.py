"""Artifact-specific exception hierarchy."""

from lexmind.exceptions import LexMindError


class ArtifactError(LexMindError):
    """Base class for artifact-layer errors."""


class ArtifactNotFoundError(ArtifactError):
    """Raised when a requested artifact does not exist."""

    def __init__(self, artifact_id: str) -> None:
        super().__init__(f"Artifact '{artifact_id}' not found")
        self.artifact_id = artifact_id


class ArtifactAlreadyExistsError(ArtifactError):
    """Raised when registering an artifact that already exists."""

    def __init__(self, artifact_id: str) -> None:
        super().__init__(f"Artifact '{artifact_id}' already exists")
        self.artifact_id = artifact_id


class ArtifactValidationError(ArtifactError):
    """Raised when artifact validation fails."""

    def __init__(self, artifact_id: str, reason: str = "") -> None:
        msg = f"Artifact '{artifact_id}' validation failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.artifact_id = artifact_id
        self.reason = reason


class ArtifactChecksumError(ArtifactError):
    """Raised when artifact checksum does not match."""

    def __init__(self, artifact_id: str, expected: str, actual: str) -> None:
        super().__init__(
            f"Artifact '{artifact_id}' checksum mismatch: "
            f"expected {expected}, got {actual}"
        )
        self.artifact_id = artifact_id
        self.expected = expected
        self.actual = actual


class ArtifactDependencyError(ArtifactError):
    """Raised when artifact dependency requirements are not met."""

    def __init__(self, artifact_id: str, missing: tuple[str, ...] = ()) -> None:
        msg = f"Artifact '{artifact_id}' has missing dependencies"
        if missing:
            msg += f": {', '.join(missing)}"
        super().__init__(msg)
        self.artifact_id = artifact_id
        self.missing = missing


class ArtifactVersionError(ArtifactError):
    """Raised when artifact versioning is violated."""

    def __init__(self, artifact_id: str, detail: str = "") -> None:
        msg = f"Artifact '{artifact_id}' version error"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.artifact_id = artifact_id
        self.detail = detail


class ArtifactStateError(ArtifactError):
    """Raised when an operation is invalid for the artifact's current state."""

    def __init__(self, artifact_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} artifact '{artifact_id}' "
            f"in state '{current_state}'"
        )
        self.artifact_id = artifact_id
        self.current_state = current_state
        self.operation = operation
