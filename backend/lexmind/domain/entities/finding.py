"""Finding entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import ConfidenceLevel
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Finding(BaseEntity):
    """Finding — a conclusion reached during an investigation."""

    investigation_id: str = ""
    title: str = ""
    description: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    supporting_document_ids: tuple[str, ...] = ()
    supporting_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.investigation_id:
            raise InvariantViolationError("Finding must belong to an investigation")
