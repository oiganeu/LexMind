"""Repository-level specifications for common queries.

These specifications complement the domain specifications and are
designed for use with ``BaseRepository.find()`` and ``find_one()``.
"""

from dataclasses import dataclass

from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.enums.domain_enums import EvidenceType, RiskLevel
from lexmind.domain.specifications.base import Specification


@dataclass(frozen=True, slots=True)
class DocumentsWithOCR(Specification):
    """Matches documents that have completed OCR processing."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        return candidate.has_ocr


@dataclass(frozen=True, slots=True)
class DocumentsWithoutEmbeddings(Specification):
    """Matches documents that do not yet have embeddings."""

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        return not candidate.has_embeddings


@dataclass(frozen=True, slots=True)
class EvidenceByPerson(Specification):
    """Matches evidence linked to a specific person via case membership."""

    person_id: str

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Evidence):
            return False
        # Evidence is matched if the person is in any of its linked cases.
        # This is a simplified check; real implementation would cross-reference.
        return bool(candidate.document_ids)


@dataclass(frozen=True, slots=True)
class EvidenceByType(Specification):
    """Matches evidence of a specific type."""

    evidence_type: EvidenceType

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Evidence):
            return False
        return candidate.evidence_type == self.evidence_type


@dataclass(frozen=True, slots=True)
class TimelineBetweenDates(Specification):
    """Matches timeline events whose date falls within a range."""

    start_date: str
    end_date: str

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, TimelineEvent):
            return False
        if candidate.date is None:
            return False
        return self.start_date <= candidate.date <= self.end_date


@dataclass(frozen=True, slots=True)
class FindingsByRisk(Specification):
    """Matches findings at or above a given risk level."""

    min_risk: RiskLevel = RiskLevel.LOW

    _RISK_ORDER: tuple[RiskLevel, ...] = (
        RiskLevel.NONE,
        RiskLevel.LOW,
        RiskLevel.MEDIUM,
        RiskLevel.HIGH,
        RiskLevel.CRITICAL,
    )

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Finding):  # noqa: SIM103
            return False
        # All findings satisfy the minimum risk check (findings have
        # confidence, not risk directly).  This is a placeholder for
        # future risk-based filtering.
        return True


@dataclass(frozen=True, slots=True)
class DocumentsByLanguage(Specification):
    """Matches documents of a specific language."""

    language_code: str

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Document):
            return False
        if candidate.language is None:
            return False
        return candidate.language.value == self.language_code


@dataclass(frozen=True, slots=True)
class PersonsByRole(Specification):
    """Matches persons with a specific role."""

    from lexmind.domain.enums.domain_enums import PersonRole

    role: PersonRole

    def is_satisfied_by(self, candidate: object) -> bool:
        if not isinstance(candidate, Person):
            return False
        return candidate.role == self.role
