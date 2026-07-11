"""Version value object (semantic versioning)."""

import re
from dataclasses import dataclass

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@dataclass(frozen=True)
class Version(ValueObject):
    """Semantic version string (MAJOR.MINOR.PATCH).

    Rules:
        * Must conform to SemVer 2.0.0.
    """

    value: str

    def __post_init__(self) -> None:
        if not _SEMVER.match(self.value):
            raise InvariantViolationError(
                "Version must be a valid SemVer 2.0.0 string"
            )

    @property
    def major(self) -> int:
        """Return the major component."""
        return int(self.value.split(".")[0])

    @property
    def minor(self) -> int:
        """Return the minor component."""
        return int(self.value.split(".")[1])

    @property
    def patch(self) -> int:
        """Return the patch component."""
        return int(self.value.split(".")[2])

    def next_major(self) -> "Version":
        """Return the next major version."""
        return Version(f"{self.major + 1}.0.0")

    def next_minor(self) -> "Version":
        """Return the next minor version."""
        return Version(f"{self.major}.{self.minor + 1}.0")

    def next_patch(self) -> "Version":
        """Return the next patch version."""
        return Version(f"{self.major}.{self.minor}.{self.patch + 1}")
