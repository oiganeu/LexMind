"""Investigation entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Investigation(BaseEntity):
    """Investigation — a structured inquiry within a case."""

    case_id: str = ""
    title: str = ""
    description: str = ""
    lead_investigator_id: str | None = None
    document_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    is_completed: bool = False

    def __post_init__(self) -> None:
        if not self.case_id:
            raise InvariantViolationError("Investigation must belong to a case")

    def add_document(self, document_id: str) -> None:
        """Link a document to this investigation."""
        if document_id not in self.document_ids:
            self.document_ids = (*self.document_ids, document_id)
            self.touch()

    def add_finding(self, finding_id: str) -> None:
        """Record a finding."""
        if finding_id not in self.finding_ids:
            self.finding_ids = (*self.finding_ids, finding_id)
            self.touch()

    def complete(self) -> None:
        """Mark the investigation as completed."""
        self.is_completed = True
        self.touch()
