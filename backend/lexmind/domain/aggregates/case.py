"""Case aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.case import Case
from lexmind.domain.enums.domain_enums import CaseStatus
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class CaseAggregate:
    """Case aggregate root.

    Manages the lifecycle of a legal case and enforces invariants
    across documents, evidence, and persons linked to it.
    """

    case: Case = field(default_factory=Case)
    _statement_ids: tuple[str, ...] = field(default_factory=tuple)
    _timeline_event_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Return the case ID."""
        return self.case.id

    @property
    def title(self) -> str:
        """Return the case title."""
        return self.case.title

    @property
    def status(self) -> CaseStatus:
        """Return the case status."""
        return self.case.status

    @property
    def document_count(self) -> int:
        """Return the number of linked documents."""
        return len(self.case.document_ids)

    @property
    def evidence_count(self) -> int:
        """Return the number of linked evidence items."""
        return len(self.case.evidence_ids)

    def add_document(self, document_id: str) -> None:
        """Link a document to the case."""
        self.case.add_document(document_id)

    def remove_document(self, document_id: str) -> None:
        """Unlink a document from the case."""
        self.case.remove_document(document_id)

    def add_evidence(self, evidence_id: str) -> None:
        """Link evidence to the case."""
        self.case.add_evidence(evidence_id)

    def add_person(self, person_id: str) -> None:
        """Link a person to the case."""
        self.case.add_person(person_id)

    def add_statement(self, statement_id: str) -> None:
        """Record a statement for this case."""
        if statement_id not in self._statement_ids:
            self._statement_ids = (*self._statement_ids, statement_id)
            self.case.touch()

    def add_timeline_event(self, event_id: str) -> None:
        """Record a timeline event for this case."""
        if event_id not in self._timeline_event_ids:
            self._timeline_event_ids = (*self._timeline_event_ids, event_id)
            self.case.touch()

    def close(self) -> None:
        """Close the case.

        Raises:
            InvariantViolationError: If the case has no documents.
        """
        if not self.case.document_ids:
            raise InvariantViolationError(
                "Cannot close a case with no documents"
            )
        self.case.close()

    def reopen(self) -> None:
        """Reopen a closed case."""
        self.case.reopen()
