"""Table detection plugin.

Exposes the table detection framework through the plugin system.  Wraps a
:class:`TableDetectionService` (backed by a
:class:`~lexmind.table_detection.table_detector.TableDetectorRegistry`) and
declares :class:`PluginCapability.TABLE_DETECTION`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_analyzer import LayoutAnalyzer, RuleBasedLayoutAnalyzer
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.table_detection.table_detection import TableDetectionService
from lexmind.table_detection.table_detector import (
    RuleBasedTableDetector,
    TableDetector,
    TableDetectorRegistry,
)
from lexmind.table_detection.table_types import (
    TableDetectionOptions,
    TableDetectionResult,
)


class TableDetectionPlugin(BasePlugin):
    """Plugin providing table detection."""

    def __init__(
        self,
        registry: TableDetectorRegistry | None = None,
        layout_analyzer: LayoutAnalyzer | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "table-detection",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Detector registry.  Defaults to a registry pre-populated
                with the dependency-free :class:`RuleBasedTableDetector`
                (which itself uses a :class:`RuleBasedLayoutAnalyzer`).
            layout_analyzer: Layout analyzer used by the default rule-based
                detector.  Ignored when *registry* is supplied.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="Table Detection",
            version="1.0.0",
            description="Detects tables and their grids on document pages.",
            capabilities=(PluginCapability.TABLE_DETECTION,),
        )
        if registry is None:
            analyzer = layout_analyzer or RuleBasedLayoutAnalyzer()
            registry = TableDetectorRegistry()
            registry.register(RuleBasedTableDetector(analyzer))
        self._service = TableDetectionService(registry, event_bus=event_bus)

    @property
    def service(self) -> TableDetectionService:
        """Return the underlying detection service."""
        return self._service

    @property
    def registry(self) -> TableDetectorRegistry:
        """Return the detector registry."""
        return self._service.registry

    def detect(
        self,
        image_data: bytes,
        options: TableDetectionOptions | None = None,
        page_number: int = 1,
        detector_name: str | None = None,
    ) -> TableDetectionResult:
        """Detect tables in *image_data* using the service."""
        options = options or TableDetectionOptions()
        return self._service.detect(
            image_data,
            options,
            page_number=page_number,
            detector_name=detector_name,
        )

    def register_detector(self, detector: TableDetector) -> None:
        """Register an additional detector (e.g. a model-backed one)."""
        self._service.registry.register(detector)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
