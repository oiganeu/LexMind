"""Search query entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class SearchQuery(BaseEntity):
    """SearchQuery — a user-initiated search within a workspace or case."""

    workspace_id: str = ""
    case_id: str | None = None
    query_text: str = ""
    filters: dict[str, str] | None = None
    result_count: int = 0

    def __post_init__(self) -> None:
        if not self.query_text or not self.query_text.strip():
            raise InvariantViolationError("SearchQuery text must not be empty")
