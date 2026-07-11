"""Artifact registry Protocol."""

from typing import Protocol, runtime_checkable

from lexmind.artifacts.artifact import Artifact


@runtime_checkable
class ArtifactRegistry(Protocol):
    """Protocol for storing and querying artifacts.

    Implementations handle persistence, indexing, and retrieval
    of artifact records.
    """

    def register(self, artifact: Artifact) -> None:
        """Register a new artifact. Raises on duplicate."""
        ...

    def find(self, artifact_id: str) -> Artifact | None:
        """Return the artifact with *artifact_id* or None."""
        ...

    def list_all(self) -> list[Artifact]:
        """Return all registered artifacts."""
        ...

    def latest(self, workspace_id: str, artifact_type: str) -> Artifact | None:
        """Return the latest version of an artifact type in a workspace."""
        ...

    def history(self, artifact_id: str) -> list[Artifact]:
        """Return all versions of an artifact by its base ID."""
        ...

    def exists(self, artifact_id: str) -> bool:
        """Return True if an artifact with *artifact_id* is registered."""
        ...

    def find_by_type(self, artifact_type: str) -> list[Artifact]:
        """Return all artifacts of a given type."""
        ...

    def find_by_producer(self, producer: str) -> list[Artifact]:
        """Return all artifacts produced by *producer*."""
        ...

    def find_dependents(self, artifact_id: str) -> list[Artifact]:
        """Return all artifacts that depend on *artifact_id*."""
        ...

    def remove(self, artifact_id: str) -> None:
        """Remove an artifact from the registry."""
        ...
