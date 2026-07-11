"""Workspace aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class WorkspaceAggregate:
    """Workspace aggregate root.

    Encapsulates a workspace and enforces invariants across
    its contained documents, cases, and collaborators.
    """

    workspace: Workspace = field(default_factory=Workspace)
    _document_ids: tuple[str, ...] = field(default_factory=tuple)
    _case_ids: tuple[str, ...] = field(default_factory=tuple)
    _collaborator_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Return the workspace ID."""
        return self.workspace.id

    @property
    def name(self) -> str:
        """Return the workspace name."""
        return self.workspace.name

    @property
    def document_count(self) -> int:
        """Return the number of documents."""
        return len(self._document_ids)

    @property
    def case_count(self) -> int:
        """Return the number of cases."""
        return len(self._case_ids)

    def add_document(self, document_id: str) -> None:
        """Add a document to this workspace.

        Raises:
            InvariantViolationError: If the document is already in the workspace.
        """
        if document_id in self._document_ids:
            raise InvariantViolationError(
                f"Document '{document_id}' already in workspace '{self.id}'"
            )
        self._document_ids = (*self._document_ids, document_id)
        self.workspace.increment_document_count()

    def remove_document(self, document_id: str) -> None:
        """Remove a document from this workspace."""
        self._document_ids = tuple(d for d in self._document_ids if d != document_id)
        self.workspace.touch()

    def add_case(self, case_id: str) -> None:
        """Add a case to this workspace.

        Raises:
            InvariantViolationError: If the case is already in the workspace.
        """
        if case_id in self._case_ids:
            raise InvariantViolationError(
                f"Case '{case_id}' already in workspace '{self.id}'"
            )
        self._case_ids = (*self._case_ids, case_id)
        self.workspace.increment_case_count()

    def remove_case(self, case_id: str) -> None:
        """Remove a case from this workspace."""
        self._case_ids = tuple(c for c in self._case_ids if c != case_id)
        self.workspace.touch()

    def add_collaborator(self, user_id: str) -> None:
        """Add a collaborator to this workspace."""
        if user_id not in self._collaborator_ids:
            self._collaborator_ids = (*self._collaborator_ids, user_id)
            self.workspace.touch()

    def remove_collaborator(self, user_id: str) -> None:
        """Remove a collaborator from this workspace."""
        self._collaborator_ids = tuple(
            u for u in self._collaborator_ids if u != user_id
        )
        self.workspace.touch()

    def deactivate(self) -> None:
        """Deactivate the workspace."""
        self.workspace.deactivate()

    def activate(self) -> None:
        """Activate the workspace."""
        self.workspace.activate()
