"""OCR artifact value objects.

Domain types for OCR artifacts that associate OCR output with document
artifacts such as pages, images and regions.  These are engine-agnostic
and carry no storage or persistence concerns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OcrArtifact:
    """A single OCR artifact associated with a document page.

    Attributes:
        artifact_id: Unique identifier for this artifact.
        document_id: Identifier of the source document.
        page_number: 1-based page number within the document.
        image_ref: Optional reference to a page image resource.
        text: The recognised text content.
        regions: List of detected text regions.
        tables: List of detected table structures.
        created_at: Unix timestamp of creation.
    """

    artifact_id: str
    document_id: str
    page_number: int
    image_ref: str | None
    text: str
    regions: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id must not be empty")
        if not self.document_id:
            raise ValueError("document_id must not be empty")
        if self.page_number < 1:
            raise ValueError("page_number must be >= 1")


@dataclass(frozen=True, slots=True)
class OcrArtifactQuery:
    """Predicate for filtering OCR artifacts.

    Attributes:
        document_id: Restrict results to this document.
        page_number: If set, restrict to this specific page.
    """

    document_id: str
    page_number: int | None = None

    def matches(self, artifact: OcrArtifact) -> bool:
        """Return True if *artifact* satisfies this query."""
        if artifact.document_id != self.document_id:
            return False
        return self.page_number is None or artifact.page_number == self.page_number


@dataclass(frozen=True, slots=True)
class OcrArtifactOptions:
    """Behavioural options for artifact storage.

    Attributes:
        overwrite: When True an existing artifact with the same id is
            silently replaced.  When False a
            :class:`~lexmind.ocr.artifacts.artifact_repository.DuplicateArtifactError`
            is raised on collision.
    """

    overwrite: bool = False

    def allows_overwrite(self) -> bool:
        """Return True if overwrite is permitted."""
        return self.overwrite
