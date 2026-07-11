"""Case repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.case import Case
from lexmind.domain.enums.domain_enums import CaseStatus
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class CaseRepository(BaseRepository[Case], Protocol):
    """Persistence contract for Case aggregates.

    Extends BaseRepository with case-specific queries.
    """

    def find_by_workspace(self, workspace_id: str) -> list[Case]:
        """Find all cases in a workspace."""

    def find_by_status(self, status: CaseStatus) -> list[Case]:
        """Find all cases with a given status."""

    def find_by_title(self, workspace_id: str, title: str) -> Case | None:
        """Find a case by title within a workspace."""
