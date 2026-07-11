"""Case entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import CaseStatus
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Case(BaseEntity):
    """Legal case — a container for evidence, documents, and analysis.

    A case belongs to a workspace and may reference many documents.
    """

    workspace_id: str = ""
    title: str = ""
    description: str = ""
    status: CaseStatus = CaseStatus.OPEN
    document_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    person_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvariantViolationError("Case title must not be empty")
        if not self.workspace_id:
            raise InvariantViolationError("Case must belong to a workspace")

    def add_document(self, document_id: str) -> None:
        """Link a document to this case."""
        if document_id not in self.document_ids:
            self.document_ids = (*self.document_ids, document_id)
            self.touch()

    def remove_document(self, document_id: str) -> None:
        """Unlink a document from this case."""
        self.document_ids = tuple(d for d in self.document_ids if d != document_id)
        self.touch()

    def add_evidence(self, evidence_id: str) -> None:
        """Link evidence to this case."""
        if evidence_id not in self.evidence_ids:
            self.evidence_ids = (*self.evidence_ids, evidence_id)
            self.touch()

    def add_person(self, person_id: str) -> None:
        """Link a person to this case."""
        if person_id not in self.person_ids:
            self.person_ids = (*self.person_ids, person_id)
            self.touch()

    def close(self) -> None:
        """Close the case."""
        self.status = CaseStatus.CLOSED
        self.touch()

    def reopen(self) -> None:
        """Reopen a closed case."""
        if self.status == CaseStatus.CLOSED:
            self.status = CaseStatus.REOPENED
            self.touch()

    @property
    def is_active(self) -> bool:
        """Return True if the case is in an active state."""
        return self.status in (CaseStatus.OPEN, CaseStatus.ACTIVE, CaseStatus.REOPENED)
