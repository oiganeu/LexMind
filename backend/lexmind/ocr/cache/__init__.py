"""OCR Cache framework.

Caches OCR results keyed by content hash.  Ships a concrete in-memory
backend (no external dependencies).  The :class:`OcrCacheService`
orchestrates get/put/has/invalidate/clear, computes cache keys from raw
data, and publishes lifecycle events.
"""

from __future__ import annotations

from lexmind.ocr.cache.cache_backend import (
    InMemoryOcrCacheBackend,
    OcrCacheBackend,
    OcrCacheBackendNotFoundError,
    OcrCacheBackendRegistry,
)
from lexmind.ocr.cache.cache_types import (
    CachedOcrResult,
    CacheKey,
    CacheStats,
    OcrCacheOptions,
)
from lexmind.ocr.cache.ocr_cache import OcrCacheService
from lexmind.ocr.cache.ocr_cache_events import (
    OcrCacheHit,
    OcrCacheMiss,
    OcrCacheStored,
)
from lexmind.ocr.cache.ocr_cache_plugin import OcrCachePlugin

__all__ = [
    "CachedOcrResult",
    "CacheKey",
    "CacheStats",
    "InMemoryOcrCacheBackend",
    "OcrCacheBackend",
    "OcrCacheBackendNotFoundError",
    "OcrCacheBackendRegistry",
    "OcrCacheHit",
    "OcrCacheMiss",
    "OcrCacheOptions",
    "OcrCachePlugin",
    "OcrCacheService",
    "OcrCacheStored",
]
