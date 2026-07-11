"""Date range value object."""

from dataclasses import dataclass
from datetime import date

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class DateRange(ValueObject):
    """Immutable date range with start and optional end.

    Rules:
        * ``start`` must be before or equal to ``end`` (when provided).
    """

    start: date
    end: date | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.start > self.end:
            raise InvariantViolationError(
                "DateRange start must be before or equal to end"
            )

    @property
    def duration_days(self) -> int:
        """Return the number of days in this range."""
        end = self.end or date.today()
        return (end - self.start).days

    def contains(self, candidate: date) -> bool:
        """Return True if *candidate* falls inside the range."""
        if self.end is None:
            return candidate >= self.start
        return self.start <= candidate <= self.end

    def overlaps(self, other: "DateRange") -> bool:
        """Return True if two ranges overlap."""
        if self.end is None or other.end is None:
            if self.end is None and other.end is None:
                return True
            if self.end is None:
                return self.start <= other.end
            return other.start <= self.end
        return self.start <= other.end and other.start <= self.end
