"""OCR Cache plugin.

Exposes the OCR cache framework through the plugin system.  Ships the
:class:`InMemoryOcrCacheBackend` by default and registers it as the
``"in-memory"`` backend.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.cache.cache_backend import (
    InMemoryOcrCacheBackend,
    OcrCacheBackend,
    OcrCacheBackendRegistry,
)
from lexmind.ocr.cache.cache_types import CacheStats, OcrCacheOptions
from lexmind.ocr.cache.ocr_cache import OcrCacheService
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OcrCachePlugin(BasePlugin):
    """Plugin providing OCR caching."""

    def __init__(
        self,
        registry: OcrCacheBackendRegistry | None = None,
        event_bus: EventBus | None = None,
        options: OcrCacheOptions | None = None,
        plugin_id: str = "ocr-cache",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Backend registry.  Defaults to a registry with the
                in-memory backend pre-registered as ``"in-memory"``.
            event_bus: Optional bus for lifecycle events.
            options: Cache options for the default in-memory backend.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="OCR Cache",
            version="1.0.0",
            description="Caches OCR results keyed by content hash.",
            capabilities=(PluginCapability.OCR_CACHE,),
        )
        if registry is None:
            registry = OcrCacheBackendRegistry()
            registry.register("in-memory", InMemoryOcrCacheBackend(options or OcrCacheOptions()))
        self._registry = registry
        self._default_backend_name = "in-memory"
        self._event_bus = event_bus
        self._service: OcrCacheService | None = None

    @property
    def registry(self) -> OcrCacheBackendRegistry:
        """Return the backend registry."""
        return self._registry

    def register_backend(self, name: str, backend: OcrCacheBackend) -> None:
        """Register an additional cache backend."""
        self._registry.register(name, backend)

    def _ensure_service(self, backend_name: str | None = None) -> OcrCacheService:
        name = backend_name or self._default_backend_name
        backend = self._registry.get(name)
        if self._service is None or self._service not in ():
            self._service = OcrCacheService(
                backend=backend,
                event_bus=self._event_bus,
            )
        return self._service

    @property
    def service(self) -> OcrCacheService:
        """Return the underlying cache service (created on first access)."""
        if self._service is None:
            self._service = self._ensure_service()
        return self._service

    def get(self, data: bytes) -> str | None:
        """Return cached OCR text for *data*, or ``None``."""
        result = self.service.get(data)
        return result.text if result is not None else None

    def put(self, data: bytes, text: str, confidence: float = 1.0) -> None:
        """Cache *text* for *data* with optional *confidence*."""
        self.service.put(data, text=text, confidence=confidence)

    def has(self, data: bytes) -> bool:
        """Return ``True`` if *data* is cached."""
        return self.service.has(data)

    def stats(self) -> CacheStats:
        """Return cumulative cache statistics."""
        return self.service.stats()

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
