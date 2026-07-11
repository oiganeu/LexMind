"""Person repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.person import Person
from lexmind.domain.enums.domain_enums import PersonRole
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class PersonRepository(BaseRepository[Person], Protocol):
    """Persistence contract for Person entities.

    Extends BaseRepository with person-specific queries.
    """

    def find_by_name(self, first_name: str, last_name: str) -> list[Person]:
        """Find persons by name (exact or partial match)."""

    def find_by_case(self, case_id: str) -> list[Person]:
        """Find all persons linked to a case."""

    def find_by_role(self, case_id: str, role: PersonRole) -> list[Person]:
        """Find persons by role within a case."""

    def find_by_organization(self, organization_id: str) -> list[Person]:
        """Find all persons belonging to an organization."""
