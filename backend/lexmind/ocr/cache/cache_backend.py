"""Cache backends for OCR results.

Defines the ``OcrCacheBackend`` Protocol and provides an in-memory
implementation along with a simple registry.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from lexmind.ocr.cache.cache_types import CachedOcrResult, CacheKey, CacheStats, OcrCacheOptions


@runtime_checkable
class OcrCacheBackend(Protocol):
    """Contract every OCR cache backend satisfies."""

    def get(self, key: CacheKey) -> CachedOcrResult | None:
        """Retrieve the cached result for *key*, or ``None``."""
        ...

    def put(self, key: CacheKey, result: CachedOcrResult) -> None:
        """Store *result* under *key*."""
        ...

    def has(self, key: CacheKey) -> bool:
        """Return ``True`` if *key* exists in the cache."""
        ...

    def invalidate(self, key: CacheKey) -> bool:
        """Remove the entry for *key*, return ``True`` if it existed."""
        ...

    def clear(self) -> None:
        """Remove all entries."""
        ...

    def stats(self) -> CacheStats:
        """Return cumulative cache statistics."""


class InMemoryOcrCacheBackend:
    """Dict-based cache backend with optional TTL and max-entries limits.

    Eviction policy: when ``max_entries`` is reached the oldest entry
    (first inserted) is discarded (FIFO).  Expired entries are skipped
    on ``get`` and ``stats``.
    """

    def __init__(self, options: OcrCacheOptions | None = None) -> None:
        self._options = options or OcrCacheOptions()
        self._store: OrderedDict[str, CachedOcrResult] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _is_expired(self, result: CachedOcrResult) -> bool:
        return self._options.is_expired(result)

    def get(self, key: CacheKey) -> CachedOcrResult | None:
        result = self._store.get(key.digest)
        if result is None:
            self._misses += 1
            return None
        if self._is_expired(result):
            del self._store[key.digest]
            self._misses += 1
            return None
        self._hits += 1
        return result

    def put(self, key: CacheKey, result: CachedOcrResult) -> None:
        if self._options.max_entries is not None:
            while len(self._store) >= self._options.max_entries:
                self._store.popitem(last=False)
        self._store[key.digest] = result

    def has(self, key: CacheKey) -> bool:
        result = self._store.get(key.digest)
        if result is None:
            return False
        if self._is_expired(result):
            del self._store[key.digest]
            return False
        return True

    def invalidate(self, key: CacheKey) -> bool:
        if key.digest in self._store:
            del self._store[key.digest]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> CacheStats:
        now = datetime.now(UTC)
        size = 0
        for result in self._store.values():
            if self._options.ttl_seconds is None or (
                now - result.created_at
            ).total_seconds() <= self._options.ttl_seconds:
                size += 1
        return CacheStats(hits=self._hits, misses=self._misses, size=size)


class OcrCacheBackendNotFoundError(ValueError):
    """Raised when the registry has no backend under the requested name."""


class OcrCacheBackendRegistry:
    """Registry of named :class:`OcrCacheBackend` instances."""

    def __init__(self) -> None:
        self._backends: dict[str, OcrCacheBackend] = {}

    def register(self, name: str, backend: OcrCacheBackend) -> None:
        """Register *backend* under *name*."""
        if not name:
            raise ValueError("name must not be empty")
        self._backends[name] = backend

    def get(self, name: str) -> OcrCacheBackend:
        """Return the backend registered under *name*."""
        backend = self._backends.get(name)
        if backend is None:
            raise OcrCacheBackendNotFoundError(
                f"No OCR cache backend registered under '{name}'"
            )
        return backend

    def has(self, name: str) -> bool:
        """Return ``True`` if a backend is registered under *name*."""
        return name in self._backends

    def registered_names(self) -> list[str]:
        """Return the sorted registered backend names."""
        return sorted(self._backends)
