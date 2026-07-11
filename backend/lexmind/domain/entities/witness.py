"""Witness entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import PersonRole


@dataclass
class Witness(BaseEntity):
    """Witness — a person who provides testimony in a case."""

    person_id: str = ""
    case_id: str = ""
    role: PersonRole = PersonRole.WITNESS
    is_credible: bool | None = None
    statement_ids: tuple[str, ...] = ()

    def add_statement(self, statement_id: str) -> None:
        """Record a statement made by this witness."""
        if statement_id not in self.statement_ids:
            self.statement_ids = (*self.statement_ids, statement_id)
            self.touch()

    def mark_credible(self) -> None:
        """Mark the witness as credible."""
        self.is_credible = True
        self.touch()

    def mark_incredible(self) -> None:
        """Mark the witness as not credible."""
        self.is_credible = False
        self.touch()
