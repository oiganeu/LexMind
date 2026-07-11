"""Citation repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.legal_citation import LegalCitation
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class CitationRepository(BaseRepository[LegalCitation], Protocol):
    """Persistence contract for LegalCitation entities.

    Extends BaseRepository with citation-specific queries.
    """

    def find_by_document(self, document_id: str) -> list[LegalCitation]:
        """Find all citations in a document."""

    def find_by_law_reference(self, law_reference_id: str) -> list[LegalCitation]:
        """Find all citations referencing a specific law."""

    def find_by_text(self, citation_text: str) -> list[LegalCitation]:
        """Find citations by text content."""
