"""Folder entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Folder(BaseEntity):
    """Folder — a virtual container for organizing documents within a workspace."""

    workspace_id: str = ""
    name: str = ""
    parent_folder_id: str | None = None
    document_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("Folder name must not be empty")
        if not self.workspace_id:
            raise InvariantViolationError("Folder must belong to a workspace")

    def add_document(self, document_id: str) -> None:
        """Place a document in this folder."""
        if document_id not in self.document_ids:
            self.document_ids = (*self.document_ids, document_id)
            self.touch()

    def remove_document(self, document_id: str) -> None:
        """Remove a document from this folder."""
        self.document_ids = tuple(d for d in self.document_ids if d != document_id)
        self.touch()
