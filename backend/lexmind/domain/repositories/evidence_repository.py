"""Evidence repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.enums.domain_enums import EvidenceType
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class EvidenceRepository(BaseRepository[Evidence], Protocol):
    """Persistence contract for Evidence entities.

    Extends BaseRepository with evidence-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[Evidence]:
        """Find all evidence items linked to a case."""

    def find_by_document(self, document_id: str) -> list[Evidence]:
        """Find all evidence items referencing a document."""

    def find_by_type(self, case_id: str, evidence_type: EvidenceType) -> list[Evidence]:
        """Find evidence by type within a case."""
