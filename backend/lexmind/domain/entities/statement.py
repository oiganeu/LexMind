"""Statement entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import StatementType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Statement(BaseEntity):
    """Statement — a spoken or written assertion made in a legal context.

    Every statement must have a source (person or document).
    """

    source_person_id: str | None = None
    source_document_id: str | None = None
    case_id: str = ""
    statement_type: StatementType = StatementType.TESTIMONY
    content: str = ""
    date_made: str | None = None
    context: str = ""

    def __post_init__(self) -> None:
        if not self.source_person_id and not self.source_document_id:
            raise InvariantViolationError(
                "Statement must have a source (person or document)"
            )

    @property
    def has_person_source(self) -> bool:
        """Return True if the source is a person."""
        return self.source_person_id is not None

    @property
    def has_document_source(self) -> bool:
        """Return True if the source is a document."""
        return self.source_document_id is not None
