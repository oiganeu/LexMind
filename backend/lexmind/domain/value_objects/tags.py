"""Tag set value object."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class TagSet(ValueObject):
    """An immutable, sorted set of tag names.

    Rules:
        * Tags must not be empty strings.
        * Tags are stored in lowercase, sorted order.
        * Maximum 50 tags.
    """

    tags: Sequence[str] | None = field(default=None)

    def __post_init__(self) -> None:
        cleaned = tuple(
            sorted({t.strip().lower() for t in (self.tags or ()) if t.strip()})
        )
        object.__setattr__(self, "tags", cleaned)
        if len(self.tags) > 50:
            raise InvariantViolationError("TagSet must contain at most 50 tags")

    def __len__(self) -> int:
        return len(self.tags)

    def __iter__(self):  # type: ignore[override]
        return iter(self.tags)

    def __contains__(self, item: str) -> bool:
        return item.lower() in self.tags

    def add(self, tag: str) -> "TagSet":
        """Return a new TagSet with the given tag added."""
        return TagSet(list(self.tags) + [tag])

    def remove(self, tag: str) -> "TagSet":
        """Return a new TagSet with the given tag removed."""
        return TagSet([t for t in self.tags if t != tag.lower()])

    def union(self, other: "TagSet") -> "TagSet":
        """Return the union of two tag sets."""
        return TagSet(list(self.tags) + list(other.tags))

    def is_subset(self, other: "TagSet") -> bool:
        """Return True if every tag in self is in other."""
        return all(t in other for t in self.tags)
