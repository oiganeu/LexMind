"""Adapter that registers OCR artifacts through the ArtifactRepository.

Translates OCR persistence requests into domain :class:`Artifact`
aggregates and delegates storage to an injected repository.  Handles
versioning: registering the same storage URI again supersedes the prior
content with a new immutable version.

No filesystem or OCR-engine specifics live here -- only artifact
lifecycle orchestration against the repository abstraction.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.artifacts.artifact_version import ArtifactVersion


class OCRArtifactRepositoryAdapter:
    """Registers and versions OCR artifacts via an ArtifactRepository."""

    def __init__(
        self,
        repository: object,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        """Initialise with a repository and optional id factory.

        Args:
            repository: Implements the ArtifactRepository interface.
            id_factory: Produces new artifact identifiers.  Injected for
                deterministic testing; defaults to random UUID4 hex.
        """
        self._repository = repository
        self._id_factory = id_factory or (lambda: uuid4().hex)

    def register(
        self,
        *,
        workspace_id: str,
        document_id: str,
        storage_uri: str,
        checksum: str,
        media_type: str,
        artifact_type: ArtifactType = ArtifactType.OCR_TEXT,
        subtype: str = "",
        producer_module: str = "ocr",
        producer_version: str = "",
        extra: dict[str, str] | None = None,
    ) -> Artifact:
        """Register an OCR artifact, versioning any existing one at *storage_uri*.

        Args:
            workspace_id: Owning workspace identifier.
            document_id: Source document identifier.
            storage_uri: Location of the persisted artifact content.
            checksum: Checksum of the persisted content.
            media_type: MIME type of the content.
            artifact_type: Domain artifact classification.
            subtype: Optional artifact subtype label.
            producer_module: Name of the producing module.
            producer_version: Version of the producing module.
            extra: Additional metadata to attach to the artifact.

        Returns:
            The persisted domain ``Artifact``.
        """
        attributes = dict(extra or {})
        existing = self._repository.get_by_uri(storage_uri)  # type: ignore[union-attr]
        if existing is not None:
            return self._version_existing(
                existing,
                checksum=checksum,
                media_type=media_type,
                producer_module=producer_module,
                producer_version=producer_version,
                extra=attributes,
            )
        return self._create_new(
            workspace_id=workspace_id,
            document_id=document_id,
            storage_uri=storage_uri,
            checksum=checksum,
            media_type=media_type,
            artifact_type=artifact_type,
            subtype=subtype,
            producer_module=producer_module,
            producer_version=producer_version,
            extra=attributes,
        )

    def _create_new(
        self,
        *,
        workspace_id: str,
        document_id: str,
        storage_uri: str,
        checksum: str,
        media_type: str,
        artifact_type: ArtifactType,
        subtype: str,
        producer_module: str,
        producer_version: str,
        extra: dict[str, str],
    ) -> Artifact:
        """Create and persist a first-version artifact."""
        artifact = Artifact(
            id=self._id_factory(),
            workspace_id=workspace_id,
            artifact_type=artifact_type,
            subtype=subtype,
            checksum=checksum,
            media_type=media_type,
            storage_uri=storage_uri,
            producer_module=producer_module,
            producer_version=producer_version,
            extra=extra,
        )
        artifact.document_id = document_id  # type: ignore[attr-defined]
        artifact.versions = [
            ArtifactVersion(
                artifact_id=artifact.id,
                version_number=1,
                checksum=checksum,
                producer_module=producer_module,
                producer_version=producer_version,
                storage_uri=storage_uri,
                media_type=media_type,
            )
        ]
        artifact.mark_available()
        return self._repository.create(artifact)  # type: ignore[union-attr]

    def _version_existing(
        self,
        artifact: Artifact,
        *,
        checksum: str,
        media_type: str,
        producer_module: str,
        producer_version: str,
        extra: dict[str, str],
    ) -> Artifact:
        """Append a new version to an existing artifact and persist it."""
        artifact.create_new_version(
            checksum=checksum,
            producer_module=producer_module,
            producer_version=producer_version,
            storage_uri=artifact.storage_uri,
            media_type=media_type,
        )
        artifact.extra.update(extra)
        return self._repository.update(artifact)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "OCRArtifactRepositoryAdapter()"
