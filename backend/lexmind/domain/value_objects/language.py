"""Language value object."""

from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Language(ValueObject):
    """ISO 639-1 language code (e.g. ``ro``, ``en``, ``de``).

    Rules:
        * Must be exactly 2 lowercase letters.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) != 2 or not self.value.isalpha():
            raise InvariantViolationError(
                "Language must be a 2-letter ISO 639-1 code"
            )
        if self.value != self.value.lower():
            raise InvariantViolationError("Language code must be lowercase")
