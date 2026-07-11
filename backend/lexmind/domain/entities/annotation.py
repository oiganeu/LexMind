"""Annotation entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Annotation(BaseEntity):
    """Annotation — an immutable note attached to a document or entity.

    Annotations are append-only and cannot be modified after creation.
    """

    document_id: str = ""
    page_number: int | None = None
    content: str = ""
    author_id: str = ""
    is_locked: bool = False

    def __post_init__(self) -> None:
        if not self.document_id:
            raise InvariantViolationError("Annotation must reference a document")
        if not self.content or not self.content.strip():
            raise InvariantViolationError("Annotation content must not be empty")

    def lock(self) -> None:
        """Permanently lock this annotation."""
        self.is_locked = True
        self.touch()
