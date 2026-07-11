"""Artifact aggregate root -- immutable processing output."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from lexmind.artifacts.artifact_exceptions import (
    ArtifactStateError,
    ArtifactValidationError,
)
from lexmind.artifacts.artifact_manifest import (
    ArtifactManifest,
    ArtifactManifestValidator,
    ManifestValidationResult,
)
from lexmind.artifacts.artifact_metadata import ArtifactMetadata
from lexmind.artifacts.artifact_state import ArtifactStatus, can_transition_artifact
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.artifacts.artifact_version import ArtifactVersion


@dataclass
class Artifact:
    """Artifact aggregate root.

    Represents an immutable product of a processing stage.
    Modifications create new versions; old versions remain available.
    """

    id: str = ""
    workspace_id: str = ""
    investigation_id: str = ""
    artifact_type: ArtifactType = ArtifactType.ORIGINAL_DOCUMENT
    subtype: str = ""
    status: ArtifactStatus = ArtifactStatus.REGISTERED
    current_version: int = 1
    producer_module: str = ""
    producer_version: str = ""
    checksum: str = ""
    media_type: str = ""
    storage_uri: str = ""
    tags: tuple[str, ...] = ()
    extra: dict[str, str] = field(default_factory=dict)
    versions: list[ArtifactVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.id:
            raise ArtifactValidationError(self.id, "artifact_id is required")
        if not self.workspace_id:
            raise ArtifactValidationError(self.id, "workspace_id is required")

    def _transition(self, target: ArtifactStatus) -> None:
        """Perform a state transition if valid."""
        if not can_transition_artifact(self.status, target):
            raise ArtifactStateError(
                self.id,
                current_state=self.status.value,
                operation=f"transition to {target.value}",
            )
        self.status = target
        self.updated_at = datetime.now(UTC)

    def mark_available(self) -> None:
        """Transition to AVAILABLE state."""
        self._transition(ArtifactStatus.AVAILABLE)

    def mark_invalid(self) -> None:
        """Transition to INVALID state."""
        self._transition(ArtifactStatus.INVALID)

    def supersede(self) -> None:
        """Transition to SUPERSEDED state."""
        self._transition(ArtifactStatus.SUPERSEDED)

    def archive(self) -> None:
        """Transition to ARCHIVED state."""
        self._transition(ArtifactStatus.ARCHIVED)

    def delete(self) -> None:
        """Transition to DELETED state (terminal)."""
        self.status = ArtifactStatus.DELETED
        self.updated_at = datetime.now(UTC)

    def create_new_version(
        self,
        checksum: str,
        producer_module: str = "",
        producer_version: str = "",
        storage_uri: str = "",
        media_type: str = "",
        notes: str = "",
    ) -> ArtifactVersion:
        """Create a new immutable version of this artifact.

        The current version is frozen and a new version record is appended.
        """
        if self.status in (ArtifactStatus.DELETED, ArtifactStatus.ARCHIVED):
            raise ArtifactStateError(
                self.id,
                current_state=self.status.value,
                operation="create new version",
            )
        self.current_version += 1
        new_ver = ArtifactVersion(
            artifact_id=self.id,
            version_number=self.current_version,
            checksum=checksum,
            producer_module=producer_module,
            producer_version=producer_version,
            storage_uri=storage_uri,
            media_type=media_type,
            notes=notes,
        )
        self.versions = (*self.versions, new_ver)
        self.checksum = checksum
        if storage_uri:
            self.storage_uri = storage_uri
        if media_type:
            self.media_type = media_type
        self.updated_at = datetime.now(UTC)
        return new_ver

    def validate_checksum(self, expected: str) -> bool:
        """Return True if current checksum matches *expected*."""
        return self.checksum == expected

    def validate_manifest(
        self,
        manifest: ArtifactManifest | None = None,
    ) -> ManifestValidationResult:
        """Validate the artifact manifest (or *manifest* argument)."""
        target = manifest or self._build_manifest()
        return ArtifactManifestValidator().validate(target)

    def _build_manifest(self) -> ArtifactManifest:
        """Build an ArtifactManifest from current state."""
        return ArtifactManifest(
            artifact_id=self.id,
            workspace_id=self.workspace_id,
            investigation_id=self.investigation_id,
            artifact_type=self.artifact_type.value,
            subtype=self.subtype,
            version=self.current_version,
            producer_module=self.producer_module,
            producer_version=self.producer_version,
            created_at=self.created_at,
            checksum=self.checksum,
            media_type=self.media_type,
            storage_uri=self.storage_uri,
            tags=self.tags,
        )

    def build_metadata(self) -> ArtifactMetadata:
        """Build an ArtifactMetadata from current state."""
        return ArtifactMetadata(
            artifact_id=self.id,
            workspace_id=self.workspace_id,
            investigation_id=self.investigation_id,
            artifact_type=self.artifact_type.value,
            subtype=self.subtype,
            version=self.current_version,
            producer_module=self.producer_module,
            producer_version=self.producer_version,
            created_at=self.created_at,
            checksum=self.checksum,
            media_type=self.media_type,
            storage_uri=self.storage_uri,
            tags=self.tags,
            extra=self.extra,
        )

    def version_history(self) -> list[ArtifactVersion]:
        """Return all recorded versions of this artifact."""
        return list(self.versions)

    def latest_version(self) -> ArtifactVersion | None:
        """Return the latest version record, or None if no versions recorded."""
        if not self.versions:
            return None
        return self.versions[-1]

    def add_tag(self, tag: str) -> None:
        """Add a tag to this artifact."""
        if tag not in self.tags:
            self.tags = (*self.tags, tag)
            self.updated_at = datetime.now(UTC)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this artifact."""
        self.tags = tuple(t for t in self.tags if t != tag)
        self.updated_at = datetime.now(UTC)
