"""Report entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Report(BaseEntity):
    """Report — a generated analysis output for a case or investigation."""

    case_id: str = ""
    investigation_id: str | None = None
    title: str = ""
    content: str = ""
    format: str = "markdown"
    generated_by: str = ""
    document_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id:
            raise InvariantViolationError("Report must belong to a case")
        if not self.title or not self.title.strip():
            raise InvariantViolationError("Report title must not be empty")

    def add_document(self, document_id: str) -> None:
        """Reference a document in this report."""
        if document_id not in self.document_ids:
            self.document_ids = (*self.document_ids, document_id)
            self.touch()
