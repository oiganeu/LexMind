"""Workspace aggregate -- lifecycle orchestrator."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.identifiers import WorkspaceId
from lexmind.workspace.workspace_exceptions import WorkspaceValidationError
from lexmind.workspace.workspace_manifest import (
    ManifestValidationResult,
    ManifestValidator,
    WorkspaceManifest,
)
from lexmind.workspace.workspace_metadata import WorkspaceMetadata
from lexmind.workspace.workspace_state import WorkspaceStatus, can_transition

WORKSPACE_DIRECTORIES: tuple[str, ...] = (
    "metadata",
    "original",
    "processed",
    "extracted",
    "cache",
    "indexes",
    "graph",
    "reports",
    "exports",
    "logs",
    "plugins",
    "temp",
)


@dataclass
class Workspace:
    """Workspace aggregate root.

    Manages the lifecycle, state transitions, and metadata of a
    single workspace.  This class contains only orchestration logic
    -- no I/O or persistence.
    """

    id: str = ""
    name: str = ""
    description: str = ""
    owner_id: str = ""
    status: WorkspaceStatus = WorkspaceStatus.CREATED
    metadata: WorkspaceMetadata | None = None
    manifest: WorkspaceManifest | None = None
    version: str = "1.0.0"
    tags: tuple[str, ...] = ()
    language: str = "ro"
    jurisdiction: str = ""
    document_count: int = 0
    case_count: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("Workspace name must not be empty")
        if not self.id:
            self.id = str(WorkspaceId(value="placeholder").value)

    @property
    def workspace_id(self) -> WorkspaceId:
        """Return the typed workspace identifier."""
        return WorkspaceId(value=self.id)

    def _transition(self, target: WorkspaceStatus) -> None:
        """Perform a state transition if valid."""
        if not can_transition(self.status, target):
            raise WorkspaceValidationError(
                self.id,
                details=(
                    f"cannot transition from '{self.status.value}' "
                    f"to '{target.value}'"
                ),
            )
        self.status = target

    def open(self) -> None:
        """Transition to OPEN state."""
        self._transition(WorkspaceStatus.OPEN)

    def activate(self) -> None:
        """Transition to ACTIVE state."""
        self._transition(WorkspaceStatus.ACTIVE)

    def set_read_only(self) -> None:
        """Transition to READ_ONLY state."""
        self._transition(WorkspaceStatus.READ_ONLY)

    def lock(self) -> None:
        """Transition to LOCKED state."""
        self._transition(WorkspaceStatus.LOCKED)

    def unlock(self) -> None:
        """Transition back to ACTIVE from LOCKED."""
        self._transition(WorkspaceStatus.ACTIVE)

    def close(self) -> None:
        """Transition to CLOSED state."""
        self._transition(WorkspaceStatus.CLOSED)

    def archive(self) -> None:
        """Transition to ARCHIVED state."""
        self._transition(WorkspaceStatus.ARCHIVED)

    def mark_corrupted(self) -> None:
        """Transition to CORRUPTED state (terminal)."""
        self.status = WorkspaceStatus.CORRUPTED

    def reopen(self) -> None:
        """Reopen a closed or archived workspace."""
        if self.status in (WorkspaceStatus.CLOSED, WorkspaceStatus.ARCHIVED):
            self.status = WorkspaceStatus.OPEN
        else:
            self._transition(WorkspaceStatus.OPEN)

    def validate_manifest(
        self,
        manifest: WorkspaceManifest | None = None,
    ) -> ManifestValidationResult:
        """Validate the workspace manifest (or *manifest* argument)."""
        target = manifest or self.manifest
        if target is None:
            return ManifestValidationResult(
                is_valid=False,
                errors=("no manifest provided",),
            )
        return ManifestValidator().validate(target)

    def validate_directories(self, existing_dirs: frozenset[str]) -> tuple[str, ...]:
        """Return a tuple of missing required directory names."""
        return tuple(d for d in WORKSPACE_DIRECTORIES if d not in existing_dirs)

    def build_metadata(self) -> WorkspaceMetadata:
        """Build a WorkspaceMetadata from current state."""

        return WorkspaceMetadata(
            workspace_id=self.id,
            name=self.name,
            description=self.description,
            version=self.version,
            owner_id=self.owner_id,
            tags=self.tags,
            language=self.language,
            jurisdiction=self.jurisdiction,
            status=self.status.value,
        )

    def increment_document_count(self) -> None:
        """Record that a document was added."""
        self.document_count += 1

    def increment_case_count(self) -> None:
        """Record that a case was added."""
        self.case_count += 1
