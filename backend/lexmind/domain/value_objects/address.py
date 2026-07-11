"""Address value object."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Address(ValueObject):
    """Physical postal address.

    Rules:
        * Street must not be empty.
        * City must not be empty.
    """

    street: str
    city: str
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None

    def __post_init__(self) -> None:
        if not self.street or not self.street.strip():
            raise InvariantViolationError("Address street must not be empty")
        if not self.city or not self.city.strip():
            raise InvariantViolationError("Address city must not be empty")

    @property
    def one_line(self) -> str:
        """Return the address as a single line."""
        parts = [self.street, self.city]
        if self.region:
            parts.append(self.region)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)
