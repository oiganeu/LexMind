"""Layout analysis plugin.

Exposes the layout analysis framework through the plugin system.  Wraps a
:class:`LayoutAnalysisService` (backed by an
:class:`~lexmind.layout.layout_analyzer.LayoutAnalyzerRegistry`) and declares
:class:`PluginCapability.LAYOUT_ANALYSIS`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.layout.layout_analysis import LayoutAnalysisService
from lexmind.layout.layout_analyzer import (
    LayoutAnalyzer,
    LayoutAnalyzerRegistry,
    RuleBasedLayoutAnalyzer,
)
from lexmind.layout.layout_types import LayoutAnalysisOptions, LayoutResult
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class LayoutAnalysisPlugin(BasePlugin):
    """Plugin providing document layout analysis."""

    def __init__(
        self,
        registry: LayoutAnalyzerRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "layout-analysis",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Analyzer registry.  Defaults to a registry pre-populated
                with the dependency-free :class:`RuleBasedLayoutAnalyzer`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="Layout Analysis",
            version="1.0.0",
            description="Detects structural regions of document pages.",
            capabilities=(PluginCapability.LAYOUT_ANALYSIS,),
        )
        if registry is None:
            registry = LayoutAnalyzerRegistry()
            registry.register(RuleBasedLayoutAnalyzer())
        self._service = LayoutAnalysisService(registry, event_bus=event_bus)

    @property
    def service(self) -> LayoutAnalysisService:
        """Return the underlying analysis service."""
        return self._service

    @property
    def registry(self) -> LayoutAnalyzerRegistry:
        """Return the analyzer registry."""
        return self._service.registry

    def analyze(
        self,
        image_data: bytes,
        options: LayoutAnalysisOptions | None = None,
        page_number: int = 1,
        analyzer_name: str | None = None,
    ) -> LayoutResult:
        """Analyze *image_data* using the service."""
        options = options or LayoutAnalysisOptions()
        return self._service.analyze(
            image_data,
            options,
            page_number=page_number,
            analyzer_name=analyzer_name,
        )

    def register_analyzer(self, analyzer: LayoutAnalyzer) -> None:
        """Register an additional analyzer (e.g. a model-backed one)."""
        self._service.registry.register(analyzer)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
