"""Base value object with immutability and equality by value."""


class ValueObject:
    """Immutable value object base class.

    All value objects must be compared by their attributes,
    not by identity.  Subclass this and add fields.

    Subclasses should use ``@dataclass(frozen=True)``.
    """

    def replace(self, **changes: object) -> "ValueObject":
        """Return a new instance with the given fields replaced.

        Uses dataclasses.replace under the hood while preserving
        the frozen constraint.
        """
        from dataclasses import replace

        return replace(self, **changes)
