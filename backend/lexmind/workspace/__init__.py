"""LexMind Workspace Engine.

Provides the workspace lifecycle framework: creation, opening,
closing, locking, migration, and isolation of workspaces.

No OCR. No AI. No database. No filesystem I/O in interfaces.
Only orchestration skeleton and protocols.
"""

from lexmind.workspace.workspace import Workspace
from lexmind.workspace.workspace_context import (
    Configuration,
    EventBus,
    Kernel,
    Logger,
    PluginManager,
    StorageProvider,
)
from lexmind.workspace.workspace_events import (
    WorkspaceArchived,
    WorkspaceClosed,
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceMigrated,
    WorkspaceOpened,
    WorkspaceValidationFailed,
)
from lexmind.workspace.workspace_exceptions import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptedError,
    WorkspaceError,
    WorkspaceLockError,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceNotOpenError,
    WorkspaceValidationError,
)
from lexmind.workspace.workspace_factory import WorkspaceFactory
from lexmind.workspace.workspace_loader import WorkspaceLoader
from lexmind.workspace.workspace_lock import SingleProcessLock, WorkspaceLock
from lexmind.workspace.workspace_manager import WorkspaceManager
from lexmind.workspace.workspace_manifest import (
    ManifestValidationResult,
    ManifestValidator,
    WorkspaceManifest,
)
from lexmind.workspace.workspace_metadata import WorkspaceMetadata
from lexmind.workspace.workspace_registry import WorkspaceRegistry
from lexmind.workspace.workspace_state import VALID_TRANSITIONS, WorkspaceStatus, can_transition

__all__ = [
    "Configuration",
    "EventBus",
    "Kernel",
    "Logger",
    "ManifestValidationResult",
    "ManifestValidator",
    "PluginManager",
    "SingleProcessLock",
    "StorageProvider",
    "VALID_TRANSITIONS",
    "Workspace",
    "WorkspaceArchived",
    "WorkspaceAlreadyOpenError",
    "WorkspaceClosed",
    "WorkspaceCorruptedError",
    "WorkspaceCreated",
    "WorkspaceDeleted",
    "WorkspaceError",
    "WorkspaceFactory",
    "WorkspaceLock",
    "WorkspaceLockError",
    "WorkspaceLoader",
    "WorkspaceManager",
    "WorkspaceManifest",
    "WorkspaceMetadata",
    "WorkspaceMigrationError",
    "WorkspaceMigrated",
    "WorkspaceNotFoundError",
    "WorkspaceNotOpenError",
    "WorkspaceOpened",
    "WorkspaceRegistry",
    "WorkspaceStatus",
    "WorkspaceValidationError",
    "WorkspaceValidationFailed",
    "can_transition",
]
