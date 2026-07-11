"""Workspace-specific exception hierarchy."""

from lexmind.exceptions import LexMindError


class WorkspaceError(LexMindError):
    """Base class for workspace-layer errors."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a requested workspace does not exist."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(f"Workspace '{workspace_id}' not found")
        self.workspace_id = workspace_id


class WorkspaceAlreadyOpenError(WorkspaceError):
    """Raised when attempting to open an already open workspace."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(f"Workspace '{workspace_id}' is already open")
        self.workspace_id = workspace_id


class WorkspaceNotOpenError(WorkspaceError):
    """Raised when performing an operation on a closed workspace."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(f"Workspace '{workspace_id}' is not open")
        self.workspace_id = workspace_id


class WorkspaceLockError(WorkspaceError):
    """Raised when a workspace lock cannot be acquired."""

    def __init__(self, workspace_id: str, reason: str = "") -> None:
        msg = f"Cannot lock workspace '{workspace_id}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.workspace_id = workspace_id
        self.reason = reason


class WorkspaceValidationError(WorkspaceError):
    """Raised when workspace validation fails."""

    def __init__(self, workspace_id: str, details: tuple[str, ...] = ()) -> None:
        msg = f"Workspace '{workspace_id}' validation failed"
        if details:
            msg += f": {'; '.join(details)}"
        super().__init__(msg)
        self.workspace_id = workspace_id
        self.details = details


class WorkspaceMigrationError(WorkspaceError):
    """Raised when workspace migration fails."""

    def __init__(self, workspace_id: str, from_version: str, to_version: str) -> None:
        super().__init__(
            f"Cannot migrate workspace '{workspace_id}' "
            f"from v{from_version} to v{to_version}"
        )
        self.workspace_id = workspace_id
        self.from_version = from_version
        self.to_version = to_version


class WorkspaceCorruptedError(WorkspaceError):
    """Raised when workspace data is inconsistent or corrupt."""

    def __init__(self, workspace_id: str, detail: str = "") -> None:
        msg = f"Workspace '{workspace_id}' is corrupted"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.workspace_id = workspace_id
        self.detail = detail
