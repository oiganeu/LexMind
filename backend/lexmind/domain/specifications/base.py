"""Specification base class.

Specifications encapsulate business rules as composable predicate objects.
They follow the Specification pattern from DDD.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Specification(ABC):
    """Base specification — a predicate over a candidate object.

    Subclass and implement ``is_satisfied_by`` to create
    concrete specifications.  Compose with ``&`` (AND),
    ``|`` (OR), and ``~`` (NOT).
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: object) -> bool:
        """Return True if *candidate* satisfies this specification."""

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(left=self, right=other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(left=self, right=other)

    def __invert__(self) -> "NotSpecification":
        return NotSpecification(spec=self)


@dataclass(frozen=True, slots=True)
class AndSpecification(Specification):
    """Composite AND specification."""

    left: Specification
    right: Specification

    def is_satisfied_by(self, candidate: object) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )


@dataclass(frozen=True, slots=True)
class OrSpecification(Specification):
    """Composite OR specification."""

    left: Specification
    right: Specification

    def is_satisfied_by(self, candidate: object) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(
            candidate
        )


@dataclass(frozen=True, slots=True)
class NotSpecification(Specification):
    """Composite NOT specification."""

    spec: Specification

    def is_satisfied_by(self, candidate: object) -> bool:
        return not self.spec.is_satisfied_by(candidate)
