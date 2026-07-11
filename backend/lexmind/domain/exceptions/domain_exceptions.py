"""Domain-layer exceptions.

These exceptions express business rule violations and are raised
by aggregates, entities, and domain services.  They carry *no*
infrastructure dependency.
"""

from lexmind.exceptions import LexMindError


class DomainError(LexMindError):
    """Base class for all domain-layer errors."""


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(DomainError):
    """Raised when creating an entity that already exists."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(f"{entity_type} '{identifier}' already exists")
        self.entity_type = entity_type
        self.identifier = identifier


class InvariantViolationError(DomainError):
    """Raised when a domain invariant is violated."""

    def __init__(self, invariant: str) -> None:
        super().__init__(f"Invariant violated: {invariant}")
        self.invariant = invariant


class WorkspaceNotFoundError(EntityNotFoundError):
    """Raised when a workspace cannot be found."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__("Workspace", workspace_id)


class CaseNotFoundError(EntityNotFoundError):
    """Raised when a case cannot be found."""

    def __init__(self, case_id: str) -> None:
        super().__init__("Case", case_id)


class DocumentNotFoundError(EntityNotFoundError):
    """Raised when a document cannot be found."""

    def __init__(self, document_id: str) -> None:
        super().__init__("Document", document_id)


class EvidenceNotFoundError(EntityNotFoundError):
    """Raised when evidence cannot be found."""

    def __init__(self, evidence_id: str) -> None:
        super().__init__("Evidence", evidence_id)


class StatementNotFoundError(EntityNotFoundError):
    """Raised when a statement cannot be found."""

    def __init__(self, statement_id: str) -> None:
        super().__init__("Statement", statement_id)


class PersonNotFoundError(EntityNotFoundError):
    """Raised when a person cannot be found."""

    def __init__(self, person_id: str) -> None:
        super().__init__("Person", person_id)


class CitationNotFoundError(EntityNotFoundError):
    """Raised when a citation cannot be found."""

    def __init__(self, citation_id: str) -> None:
        super().__init__("Citation", citation_id)


class TimelineNotFoundError(EntityNotFoundError):
    """Raised when a timeline cannot be found."""

    def __init__(self, timeline_id: str) -> None:
        super().__init__("Timeline", timeline_id)
