"""Artifact Repository -- interface and SQLite implementation.

Responsibilities:
    - CRUD operations for Artifact aggregates
    - Lookup by ID, URI, type, and document association
    - Versioning support (versions stored as JSON)
    - No business logic

Constraints:
    - Returns domain ``Artifact`` entities only.
    - No SQLAlchemy leaks outside this module.
    - Inject ``SessionManager`` via constructor.
"""

from __future__ import annotations

import json
from typing import Protocol, TypeVar, runtime_checkable

from lexmind.artifacts.artifact import Artifact
from lexmind.artifacts.artifact_state import ArtifactStatus
from lexmind.artifacts.artifact_types import ArtifactType
from lexmind.artifacts.artifact_version import ArtifactVersion
from lexmind.metadata.exceptions import EntityNotFoundError
from lexmind.metadata.models import ArtifactRow

T = TypeVar("T")


@runtime_checkable
class ArtifactRepository(Protocol[T]):
    """Interface for Artifact persistence.

    Every concrete artifact repository must implement this Protocol.
    The interface is kept minimal -- no business logic, no SQL, no ORM.
    """

    def create(self, artifact: T) -> T:
        """Persist a new artifact and return it."""

    def update(self, artifact: T) -> T:
        """Persist changes to an existing artifact and return it."""

    def get_by_id(self, artifact_id: str) -> T | None:
        """Retrieve an artifact by its primary key ID."""

    def get_by_uri(self, storage_uri: str) -> T | None:
        """Retrieve an artifact by its storage URI."""

    def list_by_document(self, document_id: str) -> list[T]:
        """Return all artifacts associated with a document."""

    def list_by_type(
        self, artifact_type: ArtifactType, workspace_id: str | None = None
    ) -> list[T]:
        """Return all artifacts of a given type, optionally filtered by workspace."""

    def latest_version(
        self, workspace_id: str, artifact_type: ArtifactType
    ) -> T | None:
        """Return the latest version of an artifact type in a workspace."""

    def delete(self, artifact_id: str) -> None:
        """Permanently remove an artifact from the store."""


class SqliteArtifactRepositoryImpl:
    """SQLite-backed implementation of ``ArtifactRepository``.

    Uses the metadata subsystem for session management.  All queries
    filter out deleted artifacts (``status == DELETED``).

    Versions are stored as a JSON text column and deserialized on read.
    """

    def __init__(self, session_manager: object) -> None:
        """Initialise with a session manager.

        Args:
            session_manager: Provides context-managed SQLAlchemy sessions.
        """
        self._sm = session_manager

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, artifact: Artifact) -> Artifact:
        """Persist a new artifact and return it.

        Args:
            artifact: A domain Artifact entity.

        Returns:
            The same entity (with persisted state).
        """
        row = ArtifactRow(
            id=artifact.id,
            workspace_id=artifact.workspace_id,
            document_id=getattr(artifact, "document_id", None),
            artifact_type=artifact.artifact_type.value,
            subtype=artifact.subtype,
            status=artifact.status.value,
            current_version=artifact.current_version,
            producer_module=artifact.producer_module,
            producer_version=artifact.producer_version,
            checksum=artifact.checksum,
            media_type=artifact.media_type,
            storage_uri=artifact.storage_uri,
            tags=json.dumps(list(artifact.tags)),
            extra=json.dumps(artifact.extra),
            versions=json.dumps(self._serialize_versions(artifact.versions)),
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
        with self._sm.session_scope() as session:
            session.add(row)
        return artifact

    def update(self, artifact: Artifact) -> Artifact:
        """Persist changes to an existing artifact.

        Args:
            artifact: A domain Artifact entity with updated fields.

        Returns:
            The same entity.

        Raises:
            EntityNotFoundError: If the artifact does not exist.
        """
        with self._sm.session_scope() as session:
            row = session.get(ArtifactRow, artifact.id)
            if row is None:
                raise EntityNotFoundError("Artifact", artifact.id)
            row.workspace_id = artifact.workspace_id
            row.document_id = getattr(artifact, "document_id", None)
            row.artifact_type = artifact.artifact_type.value
            row.subtype = artifact.subtype
            row.status = artifact.status.value
            row.current_version = artifact.current_version
            row.producer_module = artifact.producer_module
            row.producer_version = artifact.producer_version
            row.checksum = artifact.checksum
            row.media_type = artifact.media_type
            row.storage_uri = artifact.storage_uri
            row.tags = json.dumps(list(artifact.tags))
            row.extra = json.dumps(artifact.extra)
            row.versions = json.dumps(self._serialize_versions(artifact.versions))
            row.updated_at = artifact.updated_at
        return artifact

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Retrieve an artifact by its primary key ID.

        Returns None if not found or deleted.
        """
        with self._sm.session_scope() as session:
            row = session.get(ArtifactRow, artifact_id)
            if row is None or row.status == ArtifactStatus.DELETED.value:
                return None
            return self._to_domain(row)

    def get_by_uri(self, storage_uri: str) -> Artifact | None:
        """Retrieve an artifact by its storage URI.

        Returns None if not found or deleted.
        """
        with self._sm.session_scope() as session:
            row = (
                session.query(ArtifactRow)
                .filter(
                    ArtifactRow.storage_uri == storage_uri,
                    ArtifactRow.status != ArtifactStatus.DELETED.value,
                )
                .first()
            )
            return self._to_domain(row) if row else None

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_by_document(self, document_id: str) -> list[Artifact]:
        """Return all non-deleted artifacts associated with a document."""
        with self._sm.session_scope() as session:
            rows = (
                session.query(ArtifactRow)
                .filter(
                    ArtifactRow.document_id == document_id,
                    ArtifactRow.status != ArtifactStatus.DELETED.value,
                )
                .all()
            )
            return [self._to_domain(r) for r in rows]

    def list_by_type(
        self, artifact_type: ArtifactType, workspace_id: str | None = None
    ) -> list[Artifact]:
        """Return all non-deleted artifacts of a given type.

        If workspace_id is provided, results are filtered to that workspace.
        """
        with self._sm.session_scope() as session:
            query = session.query(ArtifactRow).filter(
                ArtifactRow.artifact_type == artifact_type.value,
                ArtifactRow.status != ArtifactStatus.DELETED.value,
            )
            if workspace_id is not None:
                query = query.filter(ArtifactRow.workspace_id == workspace_id)
            rows = query.all()
            return [self._to_domain(r) for r in rows]

    def latest_version(
        self, workspace_id: str, artifact_type: ArtifactType
    ) -> Artifact | None:
        """Return the latest version of an artifact type in a workspace.

        Returns the artifact with the highest current_version for the
        given type and workspace.  Returns None if no matching artifact
        exists.
        """
        with self._sm.session_scope() as session:
            row = (
                session.query(ArtifactRow)
                .filter(
                    ArtifactRow.workspace_id == workspace_id,
                    ArtifactRow.artifact_type == artifact_type.value,
                    ArtifactRow.status != ArtifactStatus.DELETED.value,
                )
                .order_by(ArtifactRow.current_version.desc())
                .first()
            )
            return self._to_domain(row) if row else None

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, artifact_id: str) -> None:
        """Permanently remove an artifact from the store.

        Raises:
            EntityNotFoundError: If the artifact does not exist.
        """
        with self._sm.session_scope() as session:
            row = session.get(ArtifactRow, artifact_id)
            if row is None:
                raise EntityNotFoundError("Artifact", artifact_id)
            session.delete(row)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_versions(versions: tuple[ArtifactVersion, ...]) -> list[dict[str, object]]:
        """Serialize artifact versions to JSON-compatible dicts."""
        result: list[dict[str, object]] = []
        for v in versions:
            result.append(
                {
                    "artifact_id": v.artifact_id,
                    "version_number": v.version_number,
                    "checksum": v.checksum,
                    "created_at": v.created_at.isoformat(),
                    "producer_module": v.producer_module,
                    "producer_version": v.producer_version,
                    "storage_uri": v.storage_uri,
                    "media_type": v.media_type,
                    "notes": v.notes,
                }
            )
        return result

    @staticmethod
    def _deserialize_versions(raw: str) -> tuple[ArtifactVersion, ...]:
        """Deserialize JSON string to a tuple of ArtifactVersion."""
        data = json.loads(raw)
        versions: list[ArtifactVersion] = []
        for item in data:
            from datetime import datetime as dt

            created_at = dt.fromisoformat(item["created_at"])
            versions.append(
                ArtifactVersion(
                    artifact_id=item["artifact_id"],
                    version_number=item["version_number"],
                    checksum=item["checksum"],
                    created_at=created_at,
                    producer_module=item.get("producer_module", ""),
                    producer_version=item.get("producer_version", ""),
                    storage_uri=item.get("storage_uri", ""),
                    media_type=item.get("media_type", ""),
                    notes=item.get("notes", ""),
                )
            )
        return tuple(versions)

    @staticmethod
    def _to_domain(row: ArtifactRow) -> Artifact:
        """Convert an ORM row to a domain Artifact entity."""
        artifact_type = ArtifactType(row.artifact_type)
        status = ArtifactStatus(row.status)
        tags_raw: list[str] = json.loads(row.tags) if row.tags else []
        extra_raw: dict[str, str] = json.loads(row.extra) if row.extra else {}
        versions = SqliteArtifactRepositoryImpl._deserialize_versions(
            row.versions
        ) if row.versions else ()

        artifact = Artifact(
            id=row.id,
            workspace_id=row.workspace_id,
            artifact_type=artifact_type,
            subtype=row.subtype,
            status=status,
            current_version=row.current_version,
            producer_module=row.producer_module,
            producer_version=row.producer_version,
            checksum=row.checksum,
            media_type=row.media_type,
            storage_uri=row.storage_uri,
            tags=tuple(tags_raw),
            extra=extra_raw,
            versions=list(versions),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        return artifact

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "SqliteArtifactRepositoryImpl()"
