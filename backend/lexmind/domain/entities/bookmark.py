"""Bookmark entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Bookmark(BaseEntity):
    """Bookmark — a user-saved position within a document."""

    document_id: str = ""
    user_id: str = ""
    page_number: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.document_id:
            raise InvariantViolationError("Bookmark must reference a document")
