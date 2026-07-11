"""Meeting entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import MeetingType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Meeting(BaseEntity):
    """Meeting — a recorded gathering relevant to a case."""

    case_id: str = ""
    meeting_type: MeetingType = MeetingType.CONSULTATION
    title: str = ""
    date: str | None = None
    location: str = ""
    attendee_ids: tuple[str, ...] = ()
    summary: str = ""
    statement_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id:
            raise InvariantViolationError("Meeting must belong to a case")

    def add_attendee(self, person_id: str) -> None:
        """Record a person as an attendee."""
        if person_id not in self.attendee_ids:
            self.attendee_ids = (*self.attendee_ids, person_id)
            self.touch()

    def add_statement(self, statement_id: str) -> None:
        """Link a statement to this meeting."""
        if statement_id not in self.statement_ids:
            self.statement_ids = (*self.statement_ids, statement_id)
            self.touch()
