"""Image preprocessing plugin.

Exposes the preprocessing framework through the plugin system so other
plugins (e.g. the OCR pipeline) can run image preparation steps before
recognition.  Wraps an :class:`ImagePreprocessingPipeline` and declares
:class:`PluginCapability.IMAGE_PREPROCESSING`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.preprocessing.image_engine import ImageEngine
from lexmind.ocr.preprocessing.image_operation import ImageOperationRegistry
from lexmind.ocr.preprocessing.image_preprocessor import (
    ImagePreprocessingPipeline,
    ImagePreprocessor,
)
from lexmind.ocr.preprocessing.preprocessing_types import (
    PreprocessingOptions,
    PreprocessingResult,
)
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class ImagePreprocessingPlugin(BasePlugin):
    """Plugin providing composable image preprocessing."""

    def __init__(
        self,
        engine: ImageEngine,
        registry: ImageOperationRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "image-preprocessing",
    ) -> None:
        """Initialise the plugin.

        Args:
            engine: The imaging engine used by preprocessing operations.
            registry: Operation registry.  Defaults to the standard set.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        if engine is None:
            raise ValueError("engine must not be None")
        super().__init__(
            id=plugin_id,
            name="Image Preprocessing",
            version="1.0.0",
            description="Composable image preprocessing pipeline for OCR.",
            capabilities=(PluginCapability.IMAGE_PREPROCESSING,),
        )
        self._pipeline: ImagePreprocessor = ImagePreprocessingPipeline(
            engine=engine, registry=registry, event_bus=event_bus
        )

    @property
    def pipeline(self) -> ImagePreprocessor:
        """Return the underlying preprocessing pipeline."""
        return self._pipeline

    def process(
        self,
        image_data: bytes,
        options: PreprocessingOptions,
        image_id: str = "",
        workspace_id: str = "",
    ) -> PreprocessingResult:
        """Preprocess *image_data* using the pipeline."""
        return self._pipeline.process(
            image_data, options, image_id=image_id, workspace_id=workspace_id
        )

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
