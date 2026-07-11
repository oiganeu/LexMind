"""Search repository interface for semantic and full-text search."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.search_query import SearchQuery
from lexmind.domain.entities.search_result import SearchResult
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class SearchQueryRepository(BaseRepository[SearchQuery], Protocol):
    """Persistence contract for SearchQuery entities."""

    def find_by_workspace(self, workspace_id: str) -> list[SearchQuery]:
        """Find all search queries in a workspace."""

    def find_by_case(self, case_id: str) -> list[SearchQuery]:
        """Find all search queries for a case."""


@runtime_checkable
class SearchResultRepository(BaseRepository[SearchResult], Protocol):
    """Persistence contract for SearchResult entities.

    Future: Supports semantic search, full-text search, and graph search.
    """

    def find_by_query(self, query_id: str) -> list[SearchResult]:
        """Find all results for a search query, ordered by score."""

    def find_top_results(self, query_id: str, limit: int = 10) -> list[SearchResult]:
        """Find the top N results for a query by relevance score."""

    def find_by_document(self, document_id: str) -> list[SearchResult]:
        """Find all search results referencing a document."""
