"""Graph repository interface for knowledge graph relationships."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.enums.domain_enums import RelationshipType
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class GraphRepository(BaseRepository[Relationship], Protocol):
    """Persistence contract for knowledge graph relationships.

    Extends BaseRepository with graph-specific queries.
    """

    def find_by_case(self, case_id: str) -> list[Relationship]:
        """Find all relationships in a case's knowledge graph."""

    def find_connected(self, entity_id: str) -> list[Relationship]:
        """Find all relationships involving an entity (as source or target)."""

    def find_by_type(
        self, case_id: str, relationship_type: RelationshipType
    ) -> list[Relationship]:
        """Find relationships by type within a case."""

    def find_between(
        self, source_id: str, target_id: str
    ) -> list[Relationship]:
        """Find all relationships between two specific entities."""

    def find_neighbors(self, entity_id: str, max_depth: int = 1) -> list[str]:
        """Find all entity IDs reachable within max_depth hops."""
