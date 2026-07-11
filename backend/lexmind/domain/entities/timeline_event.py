"""Timeline event entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class TimelineEvent(BaseEntity):
    """Timeline event — a point or range on a chronological axis.

    Rules:
        * Must have either a ``date`` or a ``date_range_start``.
    """

    case_id: str = ""
    title: str = ""
    description: str = ""
    date: str | None = None
    date_range_start: str | None = None
    date_range_end: str | None = None
    event_order: int = 0
    source_document_ids: tuple[str, ...] = ()
    source_statement_ids: tuple[str, ...] = ()
    related_entity_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.date and not self.date_range_start:
            raise InvariantViolationError(
                "TimelineEvent requires a date or date range"
            )

    def add_source_document(self, document_id: str) -> None:
        """Link a source document."""
        if document_id not in self.source_document_ids:
            self.source_document_ids = (*self.source_document_ids, document_id)
            self.touch()

    def add_source_statement(self, statement_id: str) -> None:
        """Link a source statement."""
        if statement_id not in self.source_statement_ids:
            self.source_statement_ids = (*self.source_statement_ids, statement_id)
            self.touch()
