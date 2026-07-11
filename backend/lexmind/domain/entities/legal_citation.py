"""Legal citation entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class LegalCitation(BaseEntity):
    """LegalCitation — a reference to a specific legal provision.

    Links documents to the laws they cite.
    """

    document_id: str = ""
    law_reference_id: str | None = None
    citation_text: str = ""
    article: str | None = None
    paragraph: str | None = None
    page_number: int | None = None

    def __post_init__(self) -> None:
        if not self.citation_text or not self.citation_text.strip():
            raise InvariantViolationError("Citation text must not be empty")
