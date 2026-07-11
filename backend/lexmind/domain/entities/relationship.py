"""Relationship entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import RelationshipType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Relationship(BaseEntity):
    """Relationship — a typed link between two entities."""

    source_entity_id: str = ""
    target_entity_id: str = ""
    relationship_type: RelationshipType = RelationshipType.REFERENCE
    description: str = ""
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_entity_id:
            raise InvariantViolationError("Relationship must have a source entity")
        if not self.target_entity_id:
            raise InvariantViolationError("Relationship must have a target entity")
        if self.source_entity_id == self.target_entity_id:
            raise InvariantViolationError(
                "Relationship source and target must be different"
            )
