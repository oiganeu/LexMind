# OCR Cache (Task 43)

The **OCR Cache** framework caches OCR results keyed by content hash.
It ships a concrete in-memory backend with no external dependencies.

## Architecture

```
CacheKey.from_bytes(data, "sha256") --> digest
         |
         v
OcrCacheService  (computes key, delegates to backend, emits events)
         |
         v
OcrCacheBackend  (Protocol -- InMemoryOcrCacheBackend, etc.)
         |
         v
CachedOcrResult (key, text, confidence, created_at, metadata)
```

## Components (`lexmind/ocr/cache/`)

* `cache_types` -> `CacheKey` (content-addressed by hash digest),
  `CachedOcrResult` (stored result), `OcrCacheOptions` (TTL + max
  entries), `CacheStats` (hits, misses, size, hit_rate).
* `cache_backend` -> `OcrCacheBackend` Protocol,
  `InMemoryOcrCacheBackend` (dict-based, FIFO eviction, TTL support),
  `OcrCacheBackendRegistry` / `OcrCacheBackendNotFoundError`.
* `ocr_cache` -> `OcrCacheService` (orchestrator) with event
  publishing on get/put.
* `ocr_cache_events` -> `OcrCacheHit`, `OcrCacheMiss`, `OcrCacheStored`.
* `ocr_cache_plugin` -> `OcrCachePlugin` declaring
  `PluginCapability.OCR_CACHE`.

## Usage

```python
from lexmind.ocr.cache import OcrCachePlugin, OcrCacheOptions

plugin = OcrCachePlugin(options=OcrCacheOptions(ttl_seconds=3600))
plugin.put(b"...", text="extracted text", confidence=0.95)
text = plugin.get(b"...")
```

## Design notes

* **Content-addressed**: keys are derived from raw data via SHA-256
  (or any hashlib algorithm), so identical input always hits the cache.
* **No external deps**: the in-memory backend uses only the standard
  library.
* **No global state / singletons**: registry, service and event bus
  are injected.
