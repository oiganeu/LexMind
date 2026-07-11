"""Pydantic schemas for metadata validation at the API boundary.

These schemas validate data before it enters the repository layer.
They are decoupled from both SQLAlchemy ORM models and domain entities.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Workspace schemas
# ---------------------------------------------------------------------------


class WorkspaceCreate(BaseModel):
    """Schema for creating a new workspace."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=4096)
    owner_id: str = Field(default="", max_length=36)


class WorkspaceUpdate(BaseModel):
    """Schema for updating an existing workspace."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    is_active: bool | None = None


class WorkspaceRead(BaseModel):
    """Schema for reading workspace data from the store."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    owner_id: str
    is_active: bool
    document_count: int
    case_count: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Case schemas
# ---------------------------------------------------------------------------


class CaseCreate(BaseModel):
    """Schema for creating a new case."""

    model_config = ConfigDict(frozen=True)

    workspace_id: str = Field(..., min_length=1, max_length=36)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=4096)
    status: str = Field(default="open", max_length=50)


class CaseUpdate(BaseModel):
    """Schema for updating an existing case."""

    model_config = ConfigDict(frozen=True)

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4096)
    status: str | None = Field(default=None, max_length=50)


class CaseRead(BaseModel):
    """Schema for reading case data from the store."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    title: str
    description: str
    status: str
    document_ids: list[str]
    evidence_ids: list[str]
    person_ids: list[str]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    model_config = ConfigDict(frozen=True)

    workspace_id: str = Field(..., min_length=1, max_length=36)
    title: str = Field(default="", max_length=500)
    file_path: str | None = None
    file_hash: str | None = Field(default=None, max_length=128)
    mime_type: str = Field(default="", max_length=255)
    document_type: str = Field(default="other", max_length=50)
    status: str = Field(default="draft", max_length=50)
    processing_status: str = Field(default="pending", max_length=50)
    language: str | None = Field(default=None, max_length=10)


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""

    model_config = ConfigDict(frozen=True)

    title: str | None = Field(default=None, max_length=500)
    file_path: str | None = None
    file_hash: str | None = Field(default=None, max_length=128)
    mime_type: str | None = Field(default=None, max_length=255)
    document_type: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)
    processing_status: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)
    is_duplicate: bool | None = None
    has_ocr: bool | None = None
    has_embeddings: bool | None = None


class DocumentRead(BaseModel):
    """Schema for reading document data from the store."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    title: str
    file_path: str | None
    file_hash: str | None
    mime_type: str
    document_type: str
    status: str
    processing_status: str
    language: str | None
    case_ids: list[str]
    tag_names: list[str]
    version_count: int
    is_duplicate: bool
    has_ocr: bool
    has_embeddings: bool
    created_at: datetime
    updated_at: datetime
