"""Court decision entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import CourtLevel
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class CourtDecision(BaseEntity):
    """CourtDecision — a ruling or judgment issued by a court."""

    case_id: str = ""
    court_name: str = ""
    court_level: CourtLevel = CourtLevel.FIRST_INSTANCE
    decision_date: str = ""
    decision_text: str = ""
    judge_names: tuple[str, ...] = ()
    is_final: bool = False

    def __post_init__(self) -> None:
        if not self.court_name:
            raise InvariantViolationError("CourtDecision must have a court name")
        if not self.decision_date:
            raise InvariantViolationError("CourtDecision must have a decision date")

    def mark_final(self) -> None:
        """Mark the decision as final."""
        self.is_final = True
        self.touch()
