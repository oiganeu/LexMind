"""Report repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.report import Report
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class ReportRepository(BaseRepository[Report], Protocol):
    """Persistence contract for Report entities.

    Extends BaseRepository with report-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[Report]:
        """Find all reports for a case."""

    def find_by_investigation(self, investigation_id: str) -> list[Report]:
        """Find all reports for an investigation."""

    def find_by_format(self, case_id: str, fmt: str) -> list[Report]:
        """Find reports by format (e.g., 'markdown', 'pdf')."""
