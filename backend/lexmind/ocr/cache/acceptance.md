# OCR Cache - Acceptance Criteria (Task 43)

## AC-1: Cache key and result model
- [x] `CacheKey.from_bytes` produces a deterministic hex digest; empty
      data raises `ValueError`; supports different algorithms.
- [x] `CachedOcrResult` validates confidence in [0,1]; stores key, text,
      confidence, created_at, metadata.
- [x] `OcrCacheOptions` validates positive TTL/max_entries; `is_expired`
      checks TTL; no TTL means never expired.
- [x] `CacheStats` reports hit_rate (0.0 when no lookups).

## AC-2: Cache backend contract and in-memory implementation
- [x] `OcrCacheBackend` is a `runtime_checkable` Protocol with
      get/put/has/invalidate/clear/stats.
- [x] `InMemoryOcrCacheBackend` put/get round-trip; has returns correct
      state; invalidate removes and returns True/False; clear wipes all.
- [x] TTL: expired entries are treated as misses and removed on access.
- [x] max_entries: oldest entry evicted when limit is reached (FIFO).

## AC-3: Backend registry
- [x] `register` rejects empty names.
- [x] `get` raises `OcrCacheBackendNotFoundError` for unknown names.
- [x] `has` and `registered_names` reflect registered backends.

## AC-4: Service orchestration
- [x] `OcrCacheService.get` computes key from data, delegates to
      backend, returns result or None.
- [x] `OcrCacheHit` / `OcrCacheMiss` / `OcrCacheStored` events are
      emitted via the injected `EventBus`.
- [x] `OcrCacheService.put` then `get` returns the stored result.
- [x] Expired entry returns None from service.get.

## AC-5: Plugin integration
- [x] `OcrCachePlugin` declares `PluginCapability.OCR_CACHE`.
- [x] By default it ships with an `InMemoryOcrCacheBackend` registered
      as `"in-memory"`.
- [x] `get`/`put`/`has`/`stats` and `register_backend` delegate to the
      service/registry; `start` / `stop` transition state.
