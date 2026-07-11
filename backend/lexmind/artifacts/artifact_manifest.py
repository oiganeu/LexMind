"""Artifact manifest value object."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ArtifactManifest:
    """Serializable manifest describing an artifact.

    The manifest is the authoritative source of truth for artifact
    metadata and is stored alongside the artifact data.
    """

    artifact_id: str = ""
    workspace_id: str = ""
    investigation_id: str = ""
    artifact_type: str = ""
    subtype: str = ""
    version: int = 1
    producer_module: str = ""
    producer_version: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    checksum: str = ""
    media_type: str = ""
    storage_uri: str = ""
    dependencies: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    schema_version: str = "1.0.0"


REQUIRED_MANIFEST_FIELDS: frozenset[str] = frozenset({
    "artifact_id",
    "workspace_id",
    "artifact_type",
    "version",
    "checksum",
})


@dataclass(frozen=True)
class ManifestValidationResult:
    """Result of artifact manifest validation."""

    is_valid: bool = True
    errors: tuple[str, ...] = ()


class ArtifactManifestValidator:
    """Validates artifact manifests against the required schema."""

    SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0.0"})

    def validate(self, manifest: ArtifactManifest) -> ManifestValidationResult:
        """Validate *manifest* and return a structured result."""
        errors: list[str] = []

        if not manifest.artifact_id:
            errors.append("artifact_id is required")

        if not manifest.workspace_id:
            errors.append("workspace_id is required")

        if not manifest.artifact_type:
            errors.append("artifact_type is required")

        if manifest.version < 1:
            errors.append("version must be >= 1")

        if not manifest.checksum:
            errors.append("checksum is required")

        if manifest.schema_version not in self.SUPPORTED_SCHEMA_VERSIONS:
            errors.append(
                f"unsupported schema version '{manifest.schema_version}'"
            )

        return ManifestValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
        )
