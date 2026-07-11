"""Artifact lifecycle states and transitions."""

from enum import Enum, unique


@unique
class ArtifactStatus(Enum):
    """Lifecycle status of an artifact.

    Artifacts are immutable.  State changes reflect lifecycle
    events, not content mutations.
    """

    REGISTERED = "registered"
    AVAILABLE = "available"
    INVALID = "invalid"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


VALID_ARTIFACT_TRANSITIONS: dict[ArtifactStatus, frozenset[ArtifactStatus]] = {
    ArtifactStatus.REGISTERED: frozenset({
        ArtifactStatus.AVAILABLE,
        ArtifactStatus.INVALID,
    }),
    ArtifactStatus.AVAILABLE: frozenset({
        ArtifactStatus.SUPERSEDED,
        ArtifactStatus.ARCHIVED,
        ArtifactStatus.DELETED,
    }),
    ArtifactStatus.INVALID: frozenset({ArtifactStatus.DELETED}),
    ArtifactStatus.SUPERSEDED: frozenset({
        ArtifactStatus.ARCHIVED,
        ArtifactStatus.DELETED,
    }),
    ArtifactStatus.ARCHIVED: frozenset({ArtifactStatus.DELETED}),
    ArtifactStatus.DELETED: frozenset(),
}


def can_transition_artifact(
    source: ArtifactStatus,
    target: ArtifactStatus,
) -> bool:
    """Return True if *source* -> *target* is a valid artifact transition."""
    return target in VALID_ARTIFACT_TRANSITIONS.get(source, frozenset())
