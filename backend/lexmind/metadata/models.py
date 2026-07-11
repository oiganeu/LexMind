"""SQLAlchemy ORM models for metadata persistence.

These models map to SQLite tables and live exclusively in the
infrastructure layer.  Domain entities are never imported here;
repositories handle the conversion.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class WorkspaceRow(Base):
    """SQLite table for workspace metadata."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[str] = mapped_column(String(36), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    case_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"WorkspaceRow(id={self.id!r}, name={self.name!r})"


class CaseRow(Base):
    """SQLite table for case metadata."""

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="open")
    document_ids: Mapped[str] = mapped_column(Text, default="")
    evidence_ids: Mapped[str] = mapped_column(Text, default="")
    person_ids: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"CaseRow(id={self.id!r}, title={self.title!r})"


class DocumentRow(Base):
    """SQLite table for document metadata."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(255), default="")
    document_type: Mapped[str] = mapped_column(String(50), default="other")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    processing_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    case_ids: Mapped[str] = mapped_column(Text, default="")
    tag_names: Mapped[str] = mapped_column(Text, default="")
    version_count: Mapped[int] = mapped_column(Integer, default=0)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    has_embeddings: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"DocumentRow(id={self.id!r}, title={self.title!r})"


class ArtifactRow(Base):
    """SQLite table for artifact metadata."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    document_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subtype: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(50), default="registered")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    producer_module: Mapped[str] = mapped_column(String(255), default="")
    producer_version: Mapped[str] = mapped_column(String(50), default="")
    checksum: Mapped[str] = mapped_column(String(128), default="")
    media_type: Mapped[str] = mapped_column(String(255), default="")
    storage_uri: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    extra: Mapped[str] = mapped_column(Text, default="{}")
    versions: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"ArtifactRow(id={self.id!r}, type={self.artifact_type!r})"


class JobRow(Base):
    """SQLite table for pipeline job metadata."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    result: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"JobRow(id={self.id!r}, status={self.status!r})"
