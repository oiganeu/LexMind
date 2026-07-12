"""OCR Cache service.

The :class:`OcrCacheService` is the primary entry point for interacting
with the OCR cache.  It computes a :class:`CacheKey` from raw data,
delegates to the injected backend, and publishes lifecycle events on an
optional :class:`~lexmind.events.event_bus.EventBus`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.cache.cache_backend import OcrCacheBackend
from lexmind.ocr.cache.cache_types import CachedOcrResult, CacheKey, CacheStats
from lexmind.ocr.cache.ocr_cache_events import OcrCacheHit, OcrCacheMiss, OcrCacheStored


class OcrCacheService:
    """Orchestrates OCR cache get/put/has/invalidate/clear operations.

    Args:
        backend: The cache backend to delegate to.
        event_bus: Optional bus for publishing cache lifecycle events.
        default_algorithm: Hash algorithm used for key computation
            (default ``"sha256"``).
    """

    def __init__(
        self,
        backend: OcrCacheBackend,
        event_bus: EventBus | None = None,
        default_algorithm: str = "sha256",
    ) -> None:
        self._backend = backend
        self._event_bus = event_bus
        self._default_algorithm = default_algorithm

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[arg-type]

    def _key_from_data(self, data: bytes) -> CacheKey:
        return CacheKey.from_bytes(data, algorithm=self._default_algorithm)

    def get(self, data: bytes) -> CachedOcrResult | None:
        """Return the cached result for *data*, or ``None``.

        Emits :class:`OcrCacheHit` on success or :class:`OcrCacheMiss`
        when no valid entry exists.
        """
        key = self._key_from_data(data)
        result = self._backend.get(key)
        if result is not None:
            self._emit(OcrCacheHit(aggregate_id=key.digest))
            return result
        self._emit(OcrCacheMiss(aggregate_id=key.digest))
        return None

    def put(
        self,
        data: bytes,
        text: str,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> CachedOcrResult:
        """Store *text* in the cache keyed by *data*.

        Returns the stored :class:`CachedOcrResult` and emits
        :class:`OcrCacheStored`.
        """
        key = self._key_from_data(data)
        result = CachedOcrResult(
            key=key,
            text=text,
            confidence=confidence,
            metadata=metadata or {},
        )
        self._backend.put(key, result)
        self._emit(OcrCacheStored(aggregate_id=key.digest))
        return result

    def has(self, data: bytes) -> bool:
        """Return ``True`` if *data* has a non-expired cache entry."""
        key = self._key_from_data(data)
        return self._backend.has(key)

    def invalidate(self, data: bytes) -> bool:
        """Remove the cache entry for *data*, return ``True`` if it existed."""
        key = self._key_from_data(data)
        return self._backend.invalidate(key)

    def clear(self) -> None:
        """Remove all cache entries and reset statistics."""
        self._backend.clear()

    def stats(self) -> CacheStats:
        """Return cumulative cache statistics."""
        return self._backend.stats()
