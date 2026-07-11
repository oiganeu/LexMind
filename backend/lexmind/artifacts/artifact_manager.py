"""Artifact manager -- lifecycle orchestrator.

Coordinates creation, validation, versioning, and archival
of artifacts by delegating to the registry and dependency graph.
"""

from __future__ import annotations

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_dependency import ArtifactDependency, DependencyGraph
from lexmind.artifacts.artifact_events import (
    ArtifactArchived,
    ArtifactCreated,
    ArtifactDeleted,
    ArtifactSuperseded,
    ArtifactValidated,
)
from lexmind.artifacts.artifact_exceptions import (
    ArtifactAlreadyExistsError,
    ArtifactChecksumError,
    ArtifactNotFoundError,
)
from lexmind.artifacts.artifact_lineage import LineageTracker
from lexmind.artifacts.artifact_registry import ArtifactRegistry
from lexmind.artifacts.artifact_types import ArtifactType


class ArtifactManager:
    """Orchestrates artifact lifecycle operations.

    Delegates persistence to :class:`ArtifactRegistry` and tracks
    dependencies via :class:`DependencyGraph`.
    """

    def __init__(
        self,
        registry: ArtifactRegistry,
        event_bus: object | None = None,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._dependencies = DependencyGraph()
        self._lineage = LineageTracker(graph=self._dependencies)

    def _publish(self, event: object) -> None:
        if self._event_bus is not None and hasattr(self._event_bus, "publish"):
            self._event_bus.publish(event)

    def create_artifact(
        self,
        artifact_id: str,
        workspace_id: str,
        artifact_type: ArtifactType,
        checksum: str,
        investigation_id: str = "",
        subtype: str = "",
        producer_module: str = "",
        producer_version: str = "",
        media_type: str = "",
        storage_uri: str = "",
        tags: tuple[str, ...] = (),
    ) -> Artifact:
        """Register a new artifact."""
        if self._registry.exists(artifact_id):
            raise ArtifactAlreadyExistsError(artifact_id)

        artifact = Artifact(
            id=artifact_id,
            workspace_id=workspace_id,
            investigation_id=investigation_id,
            artifact_type=artifact_type,
            subtype=subtype,
            producer_module=producer_module,
            producer_version=producer_version,
            checksum=checksum,
            media_type=media_type,
            storage_uri=storage_uri,
            tags=tags,
        )
        self._registry.register(artifact)
        self._publish(ArtifactCreated(
            aggregate_id=artifact.id,
            artifact_type=artifact_type.value,
            producer=producer_module,
        ))
        return artifact

    def validate_artifact(self, artifact_id: str, expected_checksum: str) -> bool:
        """Validate an artifact's checksum and mark it available."""
        artifact = self._get_or_raise(artifact_id)
        if not artifact.validate_checksum(expected_checksum):
            raise ArtifactChecksumError(
                artifact_id, expected=expected_checksum, actual=artifact.checksum,
            )
        artifact.mark_available()
        self._publish(ArtifactValidated(
            aggregate_id=artifact_id,
            checksum_valid=True,
        ))
        return True

    def supersede_artifact(self, artifact_id: str) -> None:
        """Mark an artifact as superseded."""
        artifact = self._get_or_raise(artifact_id)
        artifact.supersede()
        self._publish(ArtifactSuperseded(aggregate_id=artifact_id))

    def archive_artifact(self, artifact_id: str) -> None:
        """Archive an artifact."""
        artifact = self._get_or_raise(artifact_id)
        artifact.archive()
        self._publish(ArtifactArchived(aggregate_id=artifact_id))

    def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact."""
        artifact = self._get_or_raise(artifact_id)
        artifact.delete()
        self._dependencies.remove(artifact_id)
        self._publish(ArtifactDeleted(aggregate_id=artifact_id))

    def add_dependency(
        self,
        parent_id: str,
        child_id: str,
        relationship: str = "produced_by",
    ) -> None:
        """Record that *child_id* depends on *parent_id*."""
        self._get_or_raise(parent_id)
        self._get_or_raise(child_id)
        dep = ArtifactDependency(
            parent_id=parent_id,
            child_id=child_id,
            relationship=relationship,
        )
        self._dependencies.add(dep)

    def get_children(self, artifact_id: str) -> list[Artifact]:
        """Return artifacts that depend on *artifact_id*."""
        self._get_or_raise(artifact_id)
        child_ids = self._dependencies.children(artifact_id)
        return [a for aid in child_ids if (a := self._registry.find(aid)) is not None]

    def get_parents(self, artifact_id: str) -> list[Artifact]:
        """Return artifacts that *artifact_id* depends on."""
        self._get_or_raise(artifact_id)
        parent_ids = self._dependencies.parents(artifact_id)
        return [a for aid in parent_ids if (a := self._registry.find(aid)) is not None]

    def lineage(self, artifact_id: str) -> list[str]:
        """Return the full lineage chain for *artifact_id*."""
        self._get_or_raise(artifact_id)
        return self._lineage.full_chain(artifact_id)

    def validate_dependencies(self, artifact_id: str) -> tuple[str, ...]:
        """Return IDs of missing dependencies."""
        self._get_or_raise(artifact_id)
        parent_ids = self._dependencies.parents(artifact_id)
        missing = [pid for pid in parent_ids if not self._registry.exists(pid)]
        return tuple(missing)

    def pipeline_order(self) -> list[str]:
        """Return all artifact IDs in topological order."""
        return self._dependencies.topological_order()

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Return the artifact or None."""
        return self._registry.find(artifact_id)

    def list_by_type(self, artifact_type: ArtifactType) -> list[Artifact]:
        """Return all artifacts of a given type."""
        return self._registry.find_by_type(artifact_type.value)

    def _get_or_raise(self, artifact_id: str) -> Artifact:
        artifact = self._registry.find(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        return artifact
