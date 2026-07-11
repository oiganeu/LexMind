"""Artifact version -- immutable version record."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ArtifactVersion:
    """Immutable record of a single artifact version.

    Artifacts are immutable.  Any modification creates a new
    :class:`ArtifactVersion` entry.  Old versions remain available.
    """

    artifact_id: str = ""
    version_number: int = 1
    checksum: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    producer_module: str = ""
    producer_version: str = ""
    storage_uri: str = ""
    media_type: str = ""
    notes: str = ""
