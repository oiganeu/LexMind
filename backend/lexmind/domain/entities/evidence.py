"""Evidence entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import EvidenceType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Evidence(BaseEntity):
    """Evidence — a piece of proof linked to one or more cases.

    Evidence must reference at least one document.
    """

    case_ids: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    evidence_type: EvidenceType = EvidenceType.DOCUMENTARY
    description: str = ""
    source: str = ""
    is_authentic: bool | None = None

    def __post_init__(self) -> None:
        if not self.document_ids:
            raise InvariantViolationError(
                "Evidence must reference at least one document"
            )

    def link_to_case(self, case_id: str) -> None:
        """Associate evidence with a case."""
        if case_id not in self.case_ids:
            self.case_ids = (*self.case_ids, case_id)
            self.touch()

    def add_document(self, document_id: str) -> None:
        """Link an additional document to this evidence."""
        if document_id not in self.document_ids:
            self.document_ids = (*self.document_ids, document_id)
            self.touch()

    def mark_authentic(self) -> None:
        """Mark evidence as authentic."""
        self.is_authentic = True
        self.touch()

    def mark_inauthentic(self) -> None:
        """Mark evidence as inauthentic."""
        self.is_authentic = False
        self.touch()
