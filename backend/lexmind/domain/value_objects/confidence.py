"""Confidence score value object."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class ConfidenceScore(ValueObject):
    """Confidence score in the range [0.0, 1.0].

    Rules:
        * Value must be between 0.0 and 1.0 inclusive.
    """

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise InvariantViolationError("ConfidenceScore must be in [0.0, 1.0]")

    @property
    def percentage(self) -> float:
        """Return the score as a percentage."""
        return self.value * 100.0
