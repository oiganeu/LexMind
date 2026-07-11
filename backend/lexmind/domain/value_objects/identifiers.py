"""Typed identifiers for domain entities."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Identifier(ValueObject):
    """Generic typed identifier wrapping a UUID string.

    Every aggregate root and entity receives a typed identifier
    to prevent accidental assignment of wrong ID types.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvariantViolationError("Identifier value must not be empty")


@dataclass(frozen=True)
class WorkspaceId(Identifier):
    """Identifier for a workspace aggregate."""

    pass


@dataclass(frozen=True)
class CaseId(Identifier):
    """Identifier for a case aggregate."""

    pass


@dataclass(frozen=True)
class DocumentId(Identifier):
    """Identifier for a document entity."""

    pass


@dataclass(frozen=True)
class EvidenceId(Identifier):
    """Identifier for an evidence entity."""

    pass
