"""Pagination model for repository queries."""

from dataclasses import dataclass
from enum import Enum, unique
from typing import TypeVar

T = TypeVar("T")


@unique
class SortDirection(Enum):
    """Sort direction for query results."""

    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class SortField:
    """A single sort specification."""

    field_name: str
    direction: SortDirection = SortDirection.ASC


@dataclass(frozen=True, slots=True)
class Filter:
    """A single filter condition for repository queries."""

    field_name: str
    operator: str = "eq"
    value: object = None


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Pagination request parameters.

    Attributes:
        page: 1-based page number.
        page_size: Number of items per page (max 100).
        sort_fields: Ordered list of sort specifications.
        filters: List of filter conditions.
    """

    page: int = 1
    page_size: int = 20
    sort_fields: tuple[SortField, ...] = ()
    filters: tuple[Filter, ...] = ()
    cursor: str | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("PageSize must be between 1 and 100")

    @property
    def offset(self) -> int:
        """Calculate the offset for SQL LIMIT/OFFSET style queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the page size as a limit."""
        return self.page_size


@dataclass(frozen=True, slots=True)
class PageResult[T]:
    """Paginated result set.

    Attributes:
        items: The items on this page.
        total_count: Total number of items matching the query.
        page: Current page number.
        page_size: Number of items per page.
        has_next: Whether there is a next page.
        has_previous: Whether there is a previous page.
    """

    items: tuple[T, ...] = ()
    total_count: int = 0
    page: int = 1
    page_size: int = 20

    @property
    def total_pages(self) -> int:
        """Calculate the total number of pages."""
        if self.page_size == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Return True if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Return True if there is a previous page."""
        return self.page > 1

    @property
    def is_empty(self) -> bool:
        """Return True if the page contains no items."""
        return len(self.items) == 0
