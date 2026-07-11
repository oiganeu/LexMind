"""Timeline repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class TimelineRepository(BaseRepository[TimelineEvent], Protocol):
    """Persistence contract for TimelineEvent entities.

    Extends BaseRepository with timeline-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[TimelineEvent]:
        """Find all timeline events for a case."""

    def find_by_date_range(
        self, case_id: str, start_date: str, end_date: str
    ) -> list[TimelineEvent]:
        """Find events within a date range for a case."""

    def list_ordered(self, case_id: str) -> list[TimelineEvent]:
        """Return events in chronological order for a case."""

    def find_by_source_document(self, document_id: str) -> list[TimelineEvent]:
        """Find events sourced from a specific document."""
