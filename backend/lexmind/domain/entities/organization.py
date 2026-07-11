"""Organization entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.contact import EmailAddress, PhoneNumber


@dataclass
class Organization(BaseEntity):
    """Organization — a legal entity (company, agency, court, etc.)."""

    name: str = ""
    registration_number: str | None = None
    email: EmailAddress | None = None
    phone: PhoneNumber | None = None
    parent_organization_id: str | None = None
    person_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("Organization name must not be empty")

    def add_person(self, person_id: str) -> None:
        """Associate a person with this organization."""
        if person_id not in self.person_ids:
            self.person_ids = (*self.person_ids, person_id)
            self.touch()
