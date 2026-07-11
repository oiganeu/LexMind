"""Annotation repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.annotation import Annotation
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class AnnotationRepository(BaseRepository[Annotation], Protocol):
    """Persistence contract for Annotation entities.

    Extends BaseRepository with annotation-specific queries.
    """

    def find_by_document(self, document_id: str) -> list[Annotation]:
        """Find all annotations on a document."""

    def find_by_author(self, author_id: str) -> list[Annotation]:
        """Find all annotations made by an author."""

    def find_by_page(self, document_id: str, page_number: int) -> list[Annotation]:
        """Find annotations on a specific page of a document."""

    def find_locked(self, document_id: str) -> list[Annotation]:
        """Find all locked (immutable) annotations on a document."""
