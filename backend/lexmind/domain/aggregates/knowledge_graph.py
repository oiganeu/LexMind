"""Knowledge graph aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class KnowledgeGraph:
    """KnowledgeGraph aggregate root.

    Manages relationships (edges) between entities (nodes),
    enforcing no-self-loop and uniqueness invariants.
    """

    case_id: str = ""
    _relationships: tuple[Relationship, ...] = field(default_factory=tuple)

    @property
    def relationship_count(self) -> int:
        """Return the number of relationships."""
        return len(self._relationships)

    @property
    def node_ids(self) -> tuple[str, ...]:
        """Return all unique entity IDs referenced by relationships."""
        nodes: set[str] = set()
        for rel in self._relationships:
            nodes.add(rel.source_entity_id)
            nodes.add(rel.target_entity_id)
        return tuple(sorted(nodes))

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph.

        Raises:
            InvariantViolationError: If the relationship already exists.
        """
        if any(
            r.source_entity_id == relationship.source_entity_id
            and r.target_entity_id == relationship.target_entity_id
            and r.relationship_type == relationship.relationship_type
            for r in self._relationships
        ):
            raise InvariantViolationError(
                "Duplicate relationship in knowledge graph"
            )
        self._relationships = (*self._relationships, relationship)

    def remove_relationship(self, relationship_id: str) -> None:
        """Remove a relationship by ID."""
        self._relationships = tuple(
            r for r in self._relationships if r.id != relationship_id
        )

    def relationships_from(self, entity_id: str) -> tuple[Relationship, ...]:
        """Return all relationships originating from an entity."""
        return tuple(
            r for r in self._relationships if r.source_entity_id == entity_id
        )

    def relationships_to(self, entity_id: str) -> tuple[Relationship, ...]:
        """Return all relationships targeting an entity."""
        return tuple(
            r for r in self._relationships if r.target_entity_id == entity_id
        )

    def connected_entities(self, entity_id: str) -> tuple[str, ...]:
        """Return all entities connected to the given entity."""
        connected: set[str] = set()
        for rel in self.relationships_from(entity_id):
            connected.add(rel.target_entity_id)
        for rel in self.relationships_to(entity_id):
            connected.add(rel.source_entity_id)
        return tuple(sorted(connected))
