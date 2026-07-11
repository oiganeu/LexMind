"""Tag entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class Tag(BaseEntity):
    """Tag — a user-defined label for organizing entities."""

    name: str = ""
    color: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("Tag name must not be empty")

    @property
    def normalized_name(self) -> str:
        """Return the lowercased, stripped name."""
        return self.name.strip().lower()
