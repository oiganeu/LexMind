"""Concrete specifications for domain queries."""

from dataclasses import dataclass

from lexmind.domain.entities.document import Document
from lexmind.domain.specifications.base import Specification


@dataclass(frozen=True, slots=True)
class IsDuplicate(Specification):
    """Satisfied when a document is marked as a duplicate."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        return candidate.is_duplicate


@dataclass(frozen=True, slots=True)
class HasOCR(Specification):
    """Satisfied when a document has completed OCR."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        return candidate.has_ocr


@dataclass(frozen=True, slots=True)
class IsProcessed(Specification):
    """Satisfied when a document has been fully processed."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        from lexmind.domain.enums.domain_enums import DocumentStatus

        return candidate.status == DocumentStatus.PROCESSED


@dataclass(frozen=True, slots=True)
class HasEmbeddings(Specification):
    """Satisfied when embeddings have been generated for a document."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        return candidate.has_embeddings


@dataclass(frozen=True, slots=True)
class HasTimeline(Specification):
    """Satisfied when a case has at least one timeline event."""

    def is_satisfied_by(self, candidate: object) -> bool:
        from lexmind.domain.entities.case import Case

        if not isinstance(candidate, Case):  # noqa: SIM103
            return False
        # Timeline presence is checked externally; this is a placeholder.
        return True


@dataclass(frozen=True, slots=True)
class HasGraph(Specification):
    """Satisfied when a case has at least one relationship in the knowledge graph."""

    def is_satisfied_by(self, candidate: object) -> bool:
        from lexmind.domain.entities.case import Case

        if not isinstance(candidate, Case):  # noqa: SIM103
            return False
        # Graph presence is checked externally; this is a placeholder.
        return True


@dataclass(frozen=True, slots=True)
class BelongsToWorkspace(Specification):
    """Satisfied when an entity belongs to the specified workspace."""

    workspace_id: str

    def is_satisfied_by(self, candidate: object) -> bool:
        from lexmind.domain.entities.case import Case
        from lexmind.domain.entities.document import Document

        if isinstance(candidate, Document):
            return candidate.workspace_id == self.workspace_id
        if isinstance(candidate, Case):
            return candidate.workspace_id == self.workspace_id
        return False


@dataclass(frozen=True, slots=True)
class BelongsToCase(Specification):
    """Satisfied when an entity belongs to the specified case."""

    case_id: str

    def is_satisfied_by(self, candidate: object) -> bool:
        from lexmind.domain.entities.evidence import Evidence
        from lexmind.domain.entities.statement import Statement

        if isinstance(candidate, Evidence):
            return self.case_id in candidate.case_ids
        if isinstance(candidate, Statement):
            return candidate.case_id == self.case_id
        return False
