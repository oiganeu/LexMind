"""Contact information value objects."""

import re
from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_PHONE_RE = re.compile(r"^\+?[0-9\-\s()]{7,20}$")


@dataclass(frozen=True)
class EmailAddress(ValueObject):
    """Validated email address.

    Rules:
        * Must match a basic email regex.
    """

    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise InvariantViolationError("Invalid email address format")


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """Validated phone number.

    Rules:
        * Must match a basic phone regex.
    """

    value: str

    def __post_init__(self) -> None:
        if not _PHONE_RE.match(self.value):
            raise InvariantViolationError("Invalid phone number format")
