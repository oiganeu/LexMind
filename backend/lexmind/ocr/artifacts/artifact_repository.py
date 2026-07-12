"""OCR artifact repository contract and in-memory implementation.

Provides the persistence abstraction for :class:`OcrArtifact` instances.
The :class:`ArtifactRepository` Protocol defines the public contract;
:class:`InMemoryArtifactRepository` is a dict-backed implementation
suitable for testing and scaffolding.  A :class:`ArtifactRepositoryRegistry`
allows multiple named repositories to be composed at runtime.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lexmind.ocr.artifacts.artifact_types import OcrArtifact, OcrArtifactQuery


class DuplicateArtifactError(ValueError):
    """Raised when saving an artifact that already exists and overwrite is disallowed."""


class ArtifactRepositoryNotFoundError(ValueError):
    """Raised when a named repository is not found in the registry."""


@runtime_checkable
class ArtifactRepository(Protocol):
    """Contract for OCR artifact persistence."""

    def save(self, artifact: OcrArtifact) -> None:
        """Persist *artifact*."""
        ...

    def get(self, artifact_id: str) -> OcrArtifact | None:
        """Return the artifact with *artifact_id* or ``None``."""
        ...

    def find(self, query: OcrArtifactQuery) -> list[OcrArtifact]:
        """Return artifacts matching *query*."""
        ...

    def delete(self, artifact_id: str) -> bool:
        """Remove the artifact; return True if it existed."""
        ...

    def list_all(self) -> list[OcrArtifact]:
        """Return every stored artifact."""
        ...


class InMemoryArtifactRepository:
    """Dict-backed :class:`ArtifactRepository` for testing and scaffolding.

    The repository honours the overwrite flag in
    :class:`~lexmind.ocr.artifacts.artifact_types.OcrArtifactOptions`:
    when ``overwrite=False`` and an artifact with the same id already
    exists, :class:`DuplicateArtifactError` is raised.
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, OcrArtifact] = {}

    def save(self, artifact: OcrArtifact, overwrite: bool = False) -> None:
        """Persist *artifact*, optionally replacing an existing one.

        Args:
            artifact: The artifact to persist.
            overwrite: When False and the artifact id already exists,
                raise :class:`DuplicateArtifactError`.

        Raises:
            DuplicateArtifactError: If *overwrite* is False and the id
                is already stored.
        """
        existing = self._artifacts.get(artifact.artifact_id)
        if existing is not None and not overwrite:
            raise DuplicateArtifactError(
                f"Artifact '{artifact.artifact_id}' already exists"
            )
        self._artifacts[artifact.artifact_id] = artifact

    def get(self, artifact_id: str) -> OcrArtifact | None:
        """Return the artifact with *artifact_id* or ``None``."""
        return self._artifacts.get(artifact_id)

    def find(self, query: OcrArtifactQuery) -> list[OcrArtifact]:
        """Return all artifacts matching *query*."""
        return [a for a in self._artifacts.values() if query.matches(a)]

    def delete(self, artifact_id: str) -> bool:
        """Remove the artifact; return True if it existed."""
        return self._artifacts.pop(artifact_id, None) is not None

    def list_all(self) -> list[OcrArtifact]:
        """Return every stored artifact."""
        return list(self._artifacts.values())


class ArtifactRepositoryRegistry:
    """Registry mapping names to :class:`ArtifactRepository` instances."""

    def __init__(self) -> None:
        self._repositories: dict[str, ArtifactRepository] = {}

    def register(self, name: str, repository: ArtifactRepository) -> None:
        """Register a repository under *name*.

        Args:
            name: Non-empty string identifier.
            repository: The repository instance.

        Raises:
            ValueError: If *name* is empty.
        """
        if not name:
            raise ValueError("repository name must not be empty")
        self._repositories[name] = repository

    def get(self, name: str) -> ArtifactRepository:
        """Return the repository registered under *name*.

        Raises:
            ArtifactRepositoryNotFoundError: If *name* is not registered.
        """
        repo = self._repositories.get(name)
        if repo is None:
            raise ArtifactRepositoryNotFoundError(
                f"No artifact repository registered under '{name}'"
            )
        return repo

    def has(self, name: str) -> bool:
        """Return True if a repository is registered under *name*."""
        return name in self._repositories

    def registered_names(self) -> list[str]:
        """Return the registered repository names."""
        return sorted(self._repositories)
