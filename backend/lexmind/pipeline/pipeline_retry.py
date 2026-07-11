"""Retry policy definitions for pipeline stages."""

from dataclasses import dataclass
from enum import StrEnum


class RetryStrategy(StrEnum):
    """Supported retry strategies."""

    NEVER = "never"
    IMMEDIATE = "immediate"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CUSTOM = "custom"


@dataclass(frozen=True)
class RetryPolicy:
    """Declarative retry configuration for a stage."""

    strategy: RetryStrategy = RetryStrategy.NEVER
    max_attempts: int = 1
    base_delay_seconds: float = 0.0
    max_delay_seconds: float = 60.0
    multiplier: float = 2.0

    def should_retry(self, attempt: int) -> bool:
        """Return True if another attempt is allowed after ``attempt``."""
        if self.strategy == RetryStrategy.NEVER:
            return False
        return attempt < self.max_attempts

    def delay_for(self, attempt: int) -> float:
        """Return the delay in seconds before the given 1-based attempt."""
        if self.strategy in (RetryStrategy.NEVER, RetryStrategy.IMMEDIATE):
            return 0.0
        if self.strategy == RetryStrategy.FIXED_DELAY:
            return self.base_delay_seconds
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay_seconds * (self.multiplier ** max(attempt - 1, 0))
            return min(delay, self.max_delay_seconds)
        return self.base_delay_seconds


NO_RETRY = RetryPolicy(strategy=RetryStrategy.NEVER, max_attempts=1)
