"""Artifact metadata value object."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ArtifactMetadata:
    """Immutable metadata describing an artifact.

    Captures provenance, producer information, and storage
    references without coupling to any specific storage backend.
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
    tags: tuple[str, ...] = ()
    extra: dict[str, str] = field(default_factory=dict)
