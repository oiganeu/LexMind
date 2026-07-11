"""Organization repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.organization import Organization
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class OrganizationRepository(BaseRepository[Organization], Protocol):
    """Persistence contract for Organization entities.

    Extends BaseRepository with organization-specific queries.
    """

    def find_by_name(self, name: str) -> Organization | None:
        """Find an organization by exact name."""

    def find_by_parent(self, parent_id: str) -> list[Organization]:
        """Find all child organizations of a parent."""

    def find_by_person(self, person_id: str) -> list[Organization]:
        """Find all organizations a person belongs to."""
