"""Search result entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class SearchResult(BaseEntity):
    """SearchResult — a single result returned by a search query."""

    query_id: str = ""
    document_id: str = ""
    score: float = 0.0
    snippet: str = ""
    page_number: int | None = None

    def __post_init__(self) -> None:
        if not self.query_id:
            raise InvariantViolationError("SearchResult must reference a query")
        if not self.document_id:
            raise InvariantViolationError("SearchResult must reference a document")
