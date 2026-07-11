"""File-related value objects."""

import re
from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject

_HEX40 = re.compile(r"^[a-f0-9]{40}$")


@dataclass(frozen=True)
class FileHash(ValueObject):
    """SHA-1 file hash stored as a lowercase hex string.

    Rules:
        * Must be exactly 40 hexadecimal characters.
    """

    value: str

    def __post_init__(self) -> None:
        if not _HEX40.match(self.value):
            raise InvariantViolationError(
                "FileHash must be a 40-character lowercase hex string"
            )


@dataclass(frozen=True)
class FilePath(ValueObject):
    """Relative file path inside a workspace.

    Rules:
        * Must not be empty.
        * Must not start with '/'.
        * Must not contain '..'.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise InvariantViolationError("FilePath must not be empty")
        if self.value.startswith("/"):
            raise InvariantViolationError("FilePath must be relative (no leading /)")
        if ".." in self.value:
            raise InvariantViolationError("FilePath must not contain '..'")
