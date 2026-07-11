"""Base entity with identity and timestamps."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class BaseEntity:
    """Base class for all domain entities.

    Entities are distinguished by their identity (``id``),
    not by attribute equality.  Two entities with the same
    attributes but different IDs are *not* equal.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        """Update the ``updated_at`` timestamp."""
        self.updated_at = datetime.now(UTC)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
