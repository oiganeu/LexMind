"""Document-related value objects."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class DocumentTitle(ValueObject):
    """Title of a document.

    Rules:
        * Must not be empty or whitespace-only.
        * Maximum 500 characters.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvariantViolationError("DocumentTitle must not be empty")
        if len(self.value) > 500:
            raise InvariantViolationError("DocumentTitle must be at most 500 characters")

    @property
    def normalized(self) -> str:
        """Return a collapsed, stripped version of the title."""
        return " ".join(self.value.split())
