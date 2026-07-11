"""Workspace entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.identifiers import WorkspaceId


@dataclass
class Workspace(BaseEntity):
    """Workspace — top-level organizational unit.

    A workspace groups cases, documents, and collaborators.
    Every document belongs to exactly one workspace.
    """

    name: str = ""
    description: str = ""
    owner_id: str = ""
    is_active: bool = True
    document_count: int = 0
    case_count: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("Workspace name must not be empty")

    @property
    def workspace_id(self) -> WorkspaceId:
        """Return the typed workspace identifier."""
        return WorkspaceId(value=self.id)

    def deactivate(self) -> None:
        """Mark the workspace as inactive."""
        self.is_active = False
        self.touch()

    def activate(self) -> None:
        """Mark the workspace as active."""
        self.is_active = True
        self.touch()

    def increment_document_count(self) -> None:
        """Record that a document was added."""
        self.document_count += 1
        self.touch()

    def increment_case_count(self) -> None:
        """Record that a case was added."""
        self.case_count += 1
        self.touch()
