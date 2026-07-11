"""Money value object."""

from dataclasses import dataclass
from decimal import Decimal

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Money(ValueObject):
    """Monetary amount with currency code.

    Rules:
        * Amount must be non-negative.
        * Currency must be a 3-letter ISO 4217 code.
    """

    amount: Decimal
    currency: str = "RON"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvariantViolationError("Money amount must be non-negative")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise InvariantViolationError(
                "Money currency must be a 3-letter ISO 4217 code"
            )
        if self.currency != self.currency.upper():
            raise InvariantViolationError("Money currency must be uppercase")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvariantViolationError("Cannot add Money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __mul__(self, factor: int | float | Decimal) -> "Money":
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)
