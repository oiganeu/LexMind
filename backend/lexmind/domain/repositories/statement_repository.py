"""Statement repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.statement import Statement
from lexmind.domain.enums.domain_enums import StatementType
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class StatementRepository(BaseRepository[Statement], Protocol):
    """Persistence contract for Statement entities.

    Extends BaseRepository with statement-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[Statement]:
        """Find all statements in a case."""

    def find_by_person(self, person_id: str) -> list[Statement]:
        """Find all statements made by a person."""

    def find_by_document(self, document_id: str) -> list[Statement]:
        """Find all statements sourced from a document."""

    def find_by_type(self, case_id: str, statement_type: StatementType) -> list[Statement]:
        """Find statements by type within a case."""
