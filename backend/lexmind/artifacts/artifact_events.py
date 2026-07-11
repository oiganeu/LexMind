"""Artifact lifecycle domain events."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class ArtifactCreated(DomainEvent):
    """Raised when a new artifact is registered."""

    artifact_type: str = ""
    producer: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactValidated(DomainEvent):
    """Raised when an artifact passes validation."""

    checksum_valid: bool = True


@dataclass(frozen=True, slots=True)
class ArtifactArchived(DomainEvent):
    """Raised when an artifact is archived."""


@dataclass(frozen=True, slots=True)
class ArtifactSuperseded(DomainEvent):
    """Raised when an artifact is superseded by a newer version."""

    superseded_by: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactDeleted(DomainEvent):
    """Raised when an artifact is deleted."""
