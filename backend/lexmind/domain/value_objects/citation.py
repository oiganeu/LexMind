"""Citation value object for legal references."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Citation(ValueObject):
    """A legal citation string (e.g. ``Legea nr. 286/2009``).

    Rules:
        * Must not be empty.
        * Maximum 1000 characters.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvariantViolationError("Citation must not be empty")
        if len(self.value) > 1000:
            raise InvariantViolationError("Citation must be at most 1000 characters")

    @property
    def normalized(self) -> str:
        """Return a collapsed, stripped citation."""
        return " ".join(self.value.split())
