"""Geographic and spatial value objects."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Coordinate(ValueObject):
    """A 2-D geographic coordinate (latitude, longitude).

    Rules:
        * Latitude must be in [-90, 90].
        * Longitude must be in [-180, 180].
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.latitude <= 90.0):
            raise InvariantViolationError("Latitude must be in [-90, 90]")
        if not (-180.0 <= self.longitude <= 180.0):
            raise InvariantViolationError("Longitude must be in [-180, 180]")


@dataclass(frozen=True)
class PageNumber(ValueObject):
    """1-based page number.

    Rules:
        * Must be >= 1.
    """

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvariantViolationError("PageNumber must be >= 1")


@dataclass(frozen=True)
class GeoLocation(ValueObject):
    """Named geographic location with optional coordinates."""

    name: str
    country: str | None = None
    region: str | None = None
    coordinates: Coordinate | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvariantViolationError("GeoLocation name must not be empty")
