"""Base repository interface with generic CRUD operations.

Every specific repository extends this interface with
domain-specific query methods.  The base provides the
standard persistence contract.
"""

from typing import Protocol, TypeVar, runtime_checkable

from lexmind.domain.repositories.pagination import PageRequest, PageResult
from lexmind.domain.specifications.base import Specification

T = TypeVar("T")


@runtime_checkable
class BaseRepository(Protocol[T]):
    """Generic repository interface.

    Provides standard CRUD operations plus count, paginated
    listing, and specification-based queries.

    Type Parameters:
        T: The domain entity type this repository manages.
    """

    def create(self, entity: T) -> T:
        """Persist a new entity and return it (with generated ID)."""

    def update(self, entity: T) -> T:
        """Persist changes to an existing entity and return it."""

    def delete(self, entity_id: str) -> None:
        """Remove an entity by ID."""

    def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID, or None if not found."""

    def find(self, specification: Specification) -> list[T]:
        """Find all entities matching a specification."""

    def find_one(self, specification: Specification) -> T | None:
        """Find a single entity matching a specification, or None."""

    def list_all(self) -> list[T]:
        """Return all entities of this type."""

    def list_page(self, page_request: PageRequest) -> PageResult[T]:
        """Return a paginated list of entities."""

    def count(self) -> int:
        """Return the total number of entities."""

    def count_matching(self, specification: Specification) -> int:
        """Return the count of entities matching a specification."""

    def exists(self, entity_id: str) -> bool:
        """Return True if an entity with the given ID exists."""
