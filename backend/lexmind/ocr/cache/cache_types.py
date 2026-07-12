"""Value objects for the OCR cache.

Includes the content-hash key, cached result, cache options with TTL,
and cumulative statistics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheKey:
    """Content-addressed cache key based on a hash digest.

    Attributes:
        algorithm: Hash algorithm name (e.g. ``"sha256"``).
        digest: Hex digest string.
    """

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if not self.algorithm:
            raise ValueError("algorithm must not be empty")
        if not self.digest:
            raise ValueError("digest must not be empty")

    @classmethod
    def from_bytes(
        cls, data: bytes, algorithm: str = "sha256"
    ) -> CacheKey:
        """Build a :class:`CacheKey` from raw *data* using *algorithm*."""
        if not data:
            raise ValueError("data must not be empty")
        h = hashlib.new(algorithm)
        h.update(data)
        return cls(algorithm=algorithm, digest=h.hexdigest())


@dataclass(frozen=True, slots=True)
class CachedOcrResult:
    """Stored OCR result for a content-hash key.

    Attributes:
        key: The :class:`CacheKey` this result belongs to.
        text: Extracted OCR text.
        confidence: Mean confidence of the OCR run (0-1).
        created_at: When this entry was created.
        metadata: Optional extensible metadata dict.
    """

    key: CacheKey
    text: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class OcrCacheOptions:
    """Configuration for cache entry lifetime and capacity.

    Attributes:
        ttl_seconds: Time-to-live in seconds, or ``None`` for no TTL.
        max_entries: Maximum number of entries, or ``None`` for unlimited.
    """

    ttl_seconds: int | None = None
    max_entries: int | None = None

    def __post_init__(self) -> None:
        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if self.max_entries is not None and self.max_entries <= 0:
            raise ValueError("max_entries must be positive")

    def is_expired(self, result: CachedOcrResult) -> bool:
        """Return ``True`` if *result* has outlived the configured TTL.

        When no TTL is configured the result is never considered expired.
        """
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(UTC) - result.created_at).total_seconds()
        return elapsed > self.ttl_seconds


@dataclass(frozen=True, slots=True)
class CacheStats:
    """Aggregated cache statistics.

    Attributes:
        hits: Number of successful cache lookups.
        misses: Number of failed lookups.
        size: Current number of entries in the cache.
    """

    hits: int = 0
    misses: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """Return the hit rate (0.0 -- 1.0) or 0.0 when no lookups exist."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
