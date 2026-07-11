"""Workspace manifest model and validation."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class WorkspaceManifest:
    """Serializable manifest describing a workspace on disk.

    The manifest is the authoritative source of truth for workspace
    configuration and is persisted as ``workspace.yaml``.
    """

    version: str = "1.0.0"
    workspace_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    language: str = "ro"
    default_plugins: tuple[str, ...] = ()
    enabled_features: tuple[str, ...] = ()
    storage_version: str = "1"


REQUIRED_MANIFEST_FIELDS: frozenset[str] = frozenset({
    "version",
    "workspace_id",
    "name",
    "created_at",
})


@dataclass(frozen=True)
class ManifestValidationResult:
    """Result of manifest validation."""

    is_valid: bool = True
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class ManifestValidator:
    """Validates workspace manifests against the required schema.

    Checks for required fields, valid version strings, and
    structural consistency.
    """

    SUPPORTED_VERSIONS: frozenset[str] = frozenset({"1.0.0"})

    def validate(self, manifest: WorkspaceManifest) -> ManifestValidationResult:
        """Validate *manifest* and return a structured result."""
        errors: list[str] = []
        warnings: list[str] = []

        if not manifest.workspace_id:
            errors.append("workspace_id is required")

        if not manifest.name:
            errors.append("name is required")

        if manifest.version not in self.SUPPORTED_VERSIONS:
            errors.append(
                f"unsupported manifest version '{manifest.version}' "
                f"(supported: {sorted(self.SUPPORTED_VERSIONS)})"
            )

        if not manifest.language:
            warnings.append("language is empty; default may be assumed")

        return ManifestValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
