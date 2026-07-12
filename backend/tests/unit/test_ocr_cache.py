"""Unit tests for the OCR cache framework (Task 43)."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.cache.cache_backend import (
    InMemoryOcrCacheBackend,
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
from lexmind.ocr.cache.ocr_cache_events import OcrCacheHit, OcrCacheMiss, OcrCacheStored
from lexmind.ocr.cache.ocr_cache_plugin import OcrCachePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState

# ---------------------------------------------------------------------------
# CacheKey
# ---------------------------------------------------------------------------


def test_cache_key_from_bytes_deterministic() -> None:
    k1 = CacheKey.from_bytes(b"hello")
    k2 = CacheKey.from_bytes(b"hello")
    assert k1 == k2
    assert k1.algorithm == "sha256"
    assert len(k1.digest) == 64


def test_cache_key_different_inputs() -> None:
    k1 = CacheKey.from_bytes(b"hello")
    k2 = CacheKey.from_bytes(b"world")
    assert k1 != k2


def test_cache_key_different_algorithm() -> None:
    k1 = CacheKey.from_bytes(b"hello", algorithm="md5")
    k2 = CacheKey.from_bytes(b"hello", algorithm="sha1")
    assert k1 != k2
    assert len(k1.digest) == 32
    assert len(k2.digest) == 40


def test_cache_key_empty_data_raises() -> None:
    with pytest.raises(ValueError):
        CacheKey.from_bytes(b"")


def test_cache_key_empty_algorithm_or_digest_raises() -> None:
    with pytest.raises(ValueError):
        CacheKey(algorithm="", digest="abc")
    with pytest.raises(ValueError):
        CacheKey(algorithm="sha256", digest="")


# ---------------------------------------------------------------------------
# CachedOcrResult
# ---------------------------------------------------------------------------


def test_cached_result_confidence_validation() -> None:
    key = CacheKey.from_bytes(b"data")
    CachedOcrResult(key=key, text="ok", confidence=0.0)
    CachedOcrResult(key=key, text="ok", confidence=1.0)
    with pytest.raises(ValueError):
        CachedOcrResult(key=key, text="bad", confidence=1.5)
    with pytest.raises(ValueError):
        CachedOcrResult(key=key, text="bad", confidence=-0.1)


# ---------------------------------------------------------------------------
# OcrCacheOptions
# ---------------------------------------------------------------------------


def test_options_validation() -> None:
    OcrCacheOptions(ttl_seconds=None, max_entries=None)
    OcrCacheOptions(ttl_seconds=60)
    OcrCacheOptions(max_entries=100)
    with pytest.raises(ValueError):
        OcrCacheOptions(ttl_seconds=0)
    with pytest.raises(ValueError):
        OcrCacheOptions(ttl_seconds=-1)
    with pytest.raises(ValueError):
        OcrCacheOptions(max_entries=0)
    with pytest.raises(ValueError):
        OcrCacheOptions(max_entries=-5)


def test_options_is_expired_no_ttl() -> None:
    opts = OcrCacheOptions()
    key = CacheKey.from_bytes(b"x")
    result = CachedOcrResult(key=key, text="x")
    assert not opts.is_expired(result)


def test_options_is_expired_with_ttl() -> None:
    opts = OcrCacheOptions(ttl_seconds=1)
    key = CacheKey.from_bytes(b"x")
    fresh = CachedOcrResult(key=key, text="x", created_at=datetime.now(UTC))
    assert not opts.is_expired(fresh)
    old = CachedOcrResult(key=key, text="x", created_at=datetime.now(UTC) - timedelta(seconds=5))
    assert opts.is_expired(old)


# ---------------------------------------------------------------------------
# CacheStats
# ---------------------------------------------------------------------------


def test_cache_stats_hit_rate() -> None:
    assert CacheStats().hit_rate == 0.0
    assert CacheStats(hits=5, misses=5).hit_rate == 0.5
    assert CacheStats(hits=10, misses=0).hit_rate == 1.0
    assert CacheStats(hits=0, misses=10).hit_rate == 0.0


# ---------------------------------------------------------------------------
# InMemoryOcrCacheBackend
# ---------------------------------------------------------------------------


def test_in_memory_put_get() -> None:
    backend = InMemoryOcrCacheBackend()
    key = CacheKey.from_bytes(b"data")
    result = CachedOcrResult(key=key, text="hello world")
    backend.put(key, result)
    assert backend.get(key) == result
    assert backend.has(key)


def test_in_memory_get_nonexistent() -> None:
    backend = InMemoryOcrCacheBackend()
    key = CacheKey.from_bytes(b"no-such")
    assert backend.get(key) is None
    assert not backend.has(key)


def test_in_memory_invalidate() -> None:
    backend = InMemoryOcrCacheBackend()
    key = CacheKey.from_bytes(b"data")
    backend.put(key, CachedOcrResult(key=key, text="x"))
    assert backend.invalidate(key)
    assert not backend.has(key)
    assert not backend.invalidate(key)


def test_in_memory_clear() -> None:
    backend = InMemoryOcrCacheBackend()
    k1 = CacheKey.from_bytes(b"a")
    k2 = CacheKey.from_bytes(b"b")
    backend.put(k1, CachedOcrResult(key=k1, text="a"))
    backend.put(k2, CachedOcrResult(key=k2, text="b"))
    assert backend.stats().size == 2
    backend.clear()
    assert backend.stats().size == 0
    assert backend.get(k1) is None


def test_in_memory_stats() -> None:
    backend = InMemoryOcrCacheBackend()
    assert backend.stats().hits == 0
    assert backend.stats().misses == 0
    key = CacheKey.from_bytes(b"x")
    backend.put(key, CachedOcrResult(key=key, text="x"))
    backend.get(key)
    backend.get(key)
    backend.get(CacheKey.from_bytes(b"y"))
    stats = backend.stats()
    assert stats.hits == 2
    assert stats.misses == 1


def test_in_memory_ttl_expiry() -> None:
    backend = InMemoryOcrCacheBackend(OcrCacheOptions(ttl_seconds=1))
    key = CacheKey.from_bytes(b"x")
    backend.put(key, CachedOcrResult(key=key, text="x"))
    assert backend.get(key) is not None
    time.sleep(1.1)  # wait past TTL
    assert backend.get(key) is None
    assert not backend.has(key)


def test_in_memory_max_entries() -> None:
    backend = InMemoryOcrCacheBackend(OcrCacheOptions(max_entries=2))
    k1 = CacheKey.from_bytes(b"a")
    k2 = CacheKey.from_bytes(b"b")
    k3 = CacheKey.from_bytes(b"c")
    backend.put(k1, CachedOcrResult(key=k1, text="a"))
    backend.put(k2, CachedOcrResult(key=k2, text="b"))
    backend.put(k3, CachedOcrResult(key=k3, text="c"))
    assert backend.get(k1) is None  # evicted (FIFO)
    assert backend.get(k2) is not None
    assert backend.get(k3) is not None


# ---------------------------------------------------------------------------
# OcrCacheBackendRegistry
# ---------------------------------------------------------------------------


def test_registry_register_get_has() -> None:
    registry = OcrCacheBackendRegistry()
    backend = InMemoryOcrCacheBackend()
    registry.register("mem", backend)
    assert registry.has("mem")
    assert registry.get("mem") is backend
    assert "mem" in registry.registered_names()


def test_registry_empty_name_raises() -> None:
    registry = OcrCacheBackendRegistry()
    with pytest.raises(ValueError):
        registry.register("", InMemoryOcrCacheBackend())


def test_registry_get_missing_raises() -> None:
    registry = OcrCacheBackendRegistry()
    with pytest.raises(OcrCacheBackendNotFoundError):
        registry.get("nonexistent")


def test_registry_registered_names() -> None:
    registry = OcrCacheBackendRegistry()
    registry.register("b", InMemoryOcrCacheBackend())
    registry.register("a", InMemoryOcrCacheBackend())
    assert registry.registered_names() == ["a", "b"]


# ---------------------------------------------------------------------------
# OcrCacheService
# ---------------------------------------------------------------------------


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_service_hit_miss_events() -> None:
    bus = RecordingBus()
    backend = InMemoryOcrCacheBackend()
    service = OcrCacheService(backend, event_bus=bus)
    data = b"hello"
    assert service.get(data) is None
    assert len([e for e in bus.events if isinstance(e, OcrCacheMiss)]) == 1
    service.put(data, text="hello world", confidence=0.9)
    stored = [e for e in bus.events if isinstance(e, OcrCacheStored)]
    assert len(stored) == 1
    result = service.get(data)
    assert result is not None and result.text == "hello world"
    hits = [e for e in bus.events if isinstance(e, OcrCacheHit)]
    assert len(hits) == 1


def test_service_put_then_get() -> None:
    backend = InMemoryOcrCacheBackend()
    service = OcrCacheService(backend)
    data = b"some-image"
    result = service.put(data, text="extracted text", confidence=0.95, metadata={"page": 1})
    assert result.text == "extracted text"
    assert result.confidence == 0.95
    cached = service.get(data)
    assert cached == result


def test_service_get_missing_returns_none() -> None:
    service = OcrCacheService(InMemoryOcrCacheBackend())
    assert service.get(b"nope") is None


def test_service_has() -> None:
    service = OcrCacheService(InMemoryOcrCacheBackend())
    assert not service.has(b"x")
    service.put(b"x", text="text")
    assert service.has(b"x")


def test_service_invalidate() -> None:
    service = OcrCacheService(InMemoryOcrCacheBackend())
    assert not service.invalidate(b"x")
    service.put(b"x", text="text")
    assert service.invalidate(b"x")
    assert not service.has(b"x")


def test_service_clear() -> None:
    service = OcrCacheService(InMemoryOcrCacheBackend())
    service.put(b"a", text="a")
    service.put(b"b", text="b")
    assert service.stats().size == 2
    service.clear()
    assert service.stats().size == 0


def test_service_expired_entry_returns_none() -> None:
    backend = InMemoryOcrCacheBackend(OcrCacheOptions(ttl_seconds=1))
    service = OcrCacheService(backend)
    service.put(b"x", text="will expire")
    assert service.get(b"x") is not None
    time.sleep(1.1)  # wait past TTL
    assert service.get(b"x") is None


def test_service_stats() -> None:
    backend = InMemoryOcrCacheBackend()
    service = OcrCacheService(backend)
    service.put(b"a", text="a")
    service.get(b"a")
    service.get(b"b")
    stats = service.stats()
    assert stats.hits == 1
    assert stats.misses == 1


# ---------------------------------------------------------------------------
# OcrCachePlugin
# ---------------------------------------------------------------------------


def test_plugin_capability() -> None:
    plugin = OcrCachePlugin()
    assert PluginCapability.OCR_CACHE in plugin.get_metadata().capabilities


def test_plugin_get_put_has() -> None:
    plugin = OcrCachePlugin()
    data = b"test-image"
    assert not plugin.has(data)
    plugin.put(data, text="ocr result", confidence=0.8)
    assert plugin.has(data)
    assert plugin.get(data) == "ocr result"


def test_plugin_stats() -> None:
    plugin = OcrCachePlugin()
    plugin.put(b"x", text="x")
    plugin.get(b"x")
    plugin.get(b"y")
    stats = plugin.stats()
    assert stats.hits == 1
    assert stats.misses == 1


def test_plugin_register_backend() -> None:
    plugin = OcrCachePlugin()
    custom = InMemoryOcrCacheBackend()
    plugin.register_backend("custom", custom)
    assert plugin.registry.has("custom")
    assert plugin.registry.get("custom") is custom


def test_plugin_start_stop() -> None:
    plugin = OcrCachePlugin()
    assert plugin.state == PluginState.DISCOVERED
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED
