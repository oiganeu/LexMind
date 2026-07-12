"""Image preprocessing pipeline.

The :class:`ImagePreprocessingPipeline` turns a declarative
:class:`PreprocessingOptions` into an ordered, engine-backed sequence of
:class:`ImageOperation` steps.  It owns no imaging logic itself; all pixel
work is delegated to the registered operations (and, through them, to the
injected :class:`ImageEngine`).  Lifecycle events are emitted through the
optional :class:`EventBus`.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.ocr.preprocessing.image_engine import ImageEngine
from lexmind.ocr.preprocessing.image_operation import (
    ImageOperationError,
    ImageOperationRegistry,
    build_default_registry,
)
from lexmind.ocr.preprocessing.preprocessing_events import (
    ImagePreprocessingCompleted,
    ImagePreprocessingFailed,
    ImagePreprocessingStarted,
)
from lexmind.ocr.preprocessing.preprocessing_types import (
    PreprocessingOptions,
    PreprocessingResult,
)

logger = structlog.get_logger(__name__)


class ImagePreprocessor:
    """Runs preprocessing on image bytes."""

    def process(
        self,
        image_data: bytes,
        options: PreprocessingOptions,
        image_id: str = "",
        workspace_id: str = "",
    ) -> PreprocessingResult:
        """Preprocess *image_data* according to *options*."""
        ...


class ImagePreprocessingPipeline:
    """Default preprocessing pipeline implementation."""

    def __init__(
        self,
        engine: ImageEngine,
        registry: ImageOperationRegistry | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialise with an imaging engine and optional registry/bus.

        Args:
            engine: The imaging engine used by operations.
            registry: Operation registry.  Defaults to the standard set.
            event_bus: Optional bus for lifecycle events.
        """
        self._engine = engine
        self._registry = registry or build_default_registry(engine)
        self._event_bus = event_bus

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _ordered_operations(self, options: PreprocessingOptions) -> list[str]:
        if options.enabled_operations:
            return list(options.enabled_operations)
        order: list[str] = []
        if options.grayscale:
            order.append("grayscale")
        if options.deskew:
            order.append("deskew")
        if options.denoise:
            order.append("denoise")
        if options.binarize:
            order.append("binarize")
        if options.resize_max_dim > 0:
            order.append("resize")
        return order

    def process(
        self,
        image_data: bytes,
        options: PreprocessingOptions,
        image_id: str = "",
        workspace_id: str = "",
    ) -> PreprocessingResult:
        """Preprocess *image_data* according to *options*.

        Args:
            image_data: Raw image bytes.
            options: Declarative preprocessing request.
            image_id: Optional identifier for events.
            workspace_id: Optional workspace for events.

        Returns:
            A :class:`PreprocessingResult` with the processed bytes and the
            list of applied operations.

        Raises:
            ImageOperationError: If an operation fails (the error is also
                published as :class:`ImagePreprocessingFailed`).
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        self._emit(
            ImagePreprocessingStarted(
                aggregate_id=image_id or "unknown",
                image_id=image_id,
                workspace_id=workspace_id,
            )
        )

        ordered = self._ordered_operations(options)
        current = image_data
        if not ordered:
            self._emit(
                ImagePreprocessingCompleted(
                    aggregate_id=image_id or "unknown",
                    image_id=image_id,
                    workspace_id=workspace_id,
                    applied_operations=(),
                    output_size=len(current),
                )
            )
            return PreprocessingResult(image_data=current, applied_operations=())

        applied: list[str] = []
        try:
            for name in ordered:
                operation = self._registry.get(name)
                current = operation.apply(current, options)
                applied.append(name)
            self._emit(
                ImagePreprocessingCompleted(
                    aggregate_id=image_id or "unknown",
                    image_id=image_id,
                    workspace_id=workspace_id,
                    applied_operations=tuple(applied),
                    output_size=len(current),
                )
            )
            return PreprocessingResult(image_data=current, applied_operations=tuple(applied))
        except Exception as exc:  # noqa: BLE001 - surface as preprocessing failure
            self._emit(
                ImagePreprocessingFailed(
                    aggregate_id=image_id or "unknown",
                    image_id=image_id,
                    workspace_id=workspace_id,
                    error_message=str(exc),
                )
            )
            logger.error("image_preprocessing_failed", image_id=image_id, error=str(exc))
            raise ImageOperationError(str(exc)) from exc
