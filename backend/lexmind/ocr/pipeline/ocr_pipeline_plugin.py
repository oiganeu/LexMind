"""OCR pipeline plugin.

Exposes the OCR pipeline framework through the plugin system.  Wraps an
:class:`~lexmind.ocr.pipeline.ocr_pipeline.OcrPipelineService` (backed by an
:class:`~lexmind.ocr.pipeline.pipeline_step.OcrPipelineStepRegistry`) and
declares :class:`PluginCapability.OCR_PIPELINE`.  By default it ships with an
:class:`~lexmind.ocr.pipeline.pipeline_step.IdentityPipelineStep`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.pipeline.ocr_pipeline import OcrPipelineService
from lexmind.ocr.pipeline.pipeline_step import (
    IdentityPipelineStep,
    OcrPipelineStep,
    OcrPipelineStepRegistry,
)
from lexmind.ocr.pipeline.pipeline_types import (
    OcrPipelineOptions,
    OcrPipelineResult,
)
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OcrPipelinePlugin(BasePlugin):
    """Plugin providing the OCR pipeline framework."""

    def __init__(
        self,
        registry: OcrPipelineStepRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "ocr-pipeline",
        default_sequence: tuple[str, ...] = ("identity",),
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Step registry.  Defaults to a registry pre-populated
                with the dependency-free :class:`IdentityPipelineStep`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
            default_sequence: Ordered step names used when no options are
                supplied to :meth:`run`.
        """
        super().__init__(
            id=plugin_id,
            name="OCR Pipeline",
            version="1.0.0",
            description="Runs an ordered sequence of composable OCR steps.",
            capabilities=(PluginCapability.OCR_PIPELINE,),
        )
        if registry is None:
            registry = OcrPipelineStepRegistry()
            registry.register(IdentityPipelineStep())
        self._service = OcrPipelineService(
            registry,
            event_bus=event_bus,
            default_sequence=default_sequence,
        )

    @property
    def service(self) -> OcrPipelineService:
        """Return the underlying pipeline service."""
        return self._service

    @property
    def registry(self) -> OcrPipelineStepRegistry:
        """Return the step registry."""
        return self._service.registry

    def run(
        self,
        image_data: bytes,
        options: OcrPipelineOptions | None = None,
        page_number: int = 1,
    ) -> OcrPipelineResult:
        """Run the pipeline over *image_data* using the service."""
        return self._service.run(image_data, options=options, page_number=page_number)

    def register_step(self, step: OcrPipelineStep) -> None:
        """Register an additional pipeline step."""
        self._service.registry.register(step)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
