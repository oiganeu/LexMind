"""Investigation repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.investigation import Investigation
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class InvestigationRepository(BaseRepository[Investigation], Protocol):
    """Persistence contract for Investigation entities.

    Extends BaseRepository with investigation-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[Investigation]:
        """Find all investigations in a case."""

    def find_completed(self, case_id: str) -> list[Investigation]:
        """Find all completed investigations in a case."""

    def find_active(self, case_id: str) -> list[Investigation]:
        """Find all non-completed investigations in a case."""
