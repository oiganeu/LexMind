"""Person entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import PersonRole
from lexmind.domain.value_objects.contact import EmailAddress, PhoneNumber


@dataclass
class Person(BaseEntity):
    """Person — a natural person involved in legal proceedings."""

    first_name: str = ""
    last_name: str = ""
    role: PersonRole = PersonRole.THIRD_PARTY
    email: EmailAddress | None = None
    phone: PhoneNumber | None = None
    organization_id: str | None = None
    case_ids: tuple[str, ...] = ()

    @property
    def full_name(self) -> str:
        """Return the full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def link_to_case(self, case_id: str) -> None:
        """Associate this person with a case."""
        if case_id not in self.case_ids:
            self.case_ids = (*self.case_ids, case_id)
            self.touch()
