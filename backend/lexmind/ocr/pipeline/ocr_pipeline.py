"""OCR pipeline orchestrator.

The :class:`OcrPipelineService` runs an ordered sequence of composable
:class:`~lexmind.ocr.pipeline.pipeline_step.OcrPipelineStep` instances over a
single page image, accumulates their :class:`PipelineStepResult` objects and
publishes lifecycle events on an injected :class:`~lexmind.events.event_bus.EventBus`.
A failing step triggers :class:`OcrPipelineFailed` and stops the run, re-raising
the original error.
"""

from __future__ import annotations

import time

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.ocr.pipeline.ocr_pipeline_events import (
    OcrPipelineCompleted,
    OcrPipelineFailed,
    OcrPipelineStarted,
    OcrPipelineStepCompleted,
)
from lexmind.ocr.pipeline.pipeline_step import (
    OcrPipelineStepRegistry,
    PipelineContext,
)
from lexmind.ocr.pipeline.pipeline_types import (
    OcrPipelineOptions,
    OcrPipelineResult,
    PipelineStepResult,
)

logger = structlog.get_logger(__name__)


class OcrPipelineService:
    """Default OCR pipeline orchestrator."""

    def __init__(
        self,
        registry: OcrPipelineStepRegistry,
        event_bus: EventBus | None = None,
        default_sequence: tuple[str, ...] = ("identity",),
    ) -> None:
        """Initialise with a registry and an optional bus/sequence.

        Args:
            registry: Registry of available steps.
            event_bus: Optional bus for lifecycle events.
            default_sequence: Ordered step names used when no options are
                supplied.  Defaults to a single ``identity`` step.
        """
        self._registry = registry
        self._event_bus = event_bus
        self._default_sequence = default_sequence

    @property
    def registry(self) -> OcrPipelineStepRegistry:
        """Return the step registry."""
        return self._registry

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def run(
        self,
        image_data: bytes,
        options: OcrPipelineOptions | None = None,
        page_number: int = 1,
    ) -> OcrPipelineResult:
        """Run the OCR pipeline over *image_data*.

        Args:
            image_data: Raw page image bytes.
            options: Optional step sequence/selection.  When ``None`` the
                configured :attr:`default_sequence` is used.
            page_number: Page identifier for events and the result.

        Returns:
            An :class:`OcrPipelineResult` aggregating every step outcome.

        Raises:
            ValueError: If *image_data* is empty.
            OcrPipelineStepNotFoundError: If a requested step is not registered.
            Exception: Re-raises any error raised by a step after publishing
                :class:`OcrPipelineFailed`.
        """
        if not image_data:
            raise ValueError("image_data must not be empty")

        names = options.step_names if options is not None else self._default_sequence

        self._emit(
            OcrPipelineStarted(
                aggregate_id=str(page_number),
                page_number=page_number,
                step_names=tuple(names),
            )
        )

        started = time.perf_counter()
        context = PipelineContext(image_data=image_data, page_number=page_number)
        results: list[PipelineStepResult] = []
        final_text = ""
        name = ""
        try:
            for name in names:
                step = self._registry.get(name)
                step_start = time.perf_counter()
                result = step.process(context)
                duration = (time.perf_counter() - step_start) * 1000.0
                step_result = PipelineStepResult(
                    step_name=result.step_name,
                    data=result.data,
                    metadata=result.metadata,
                    duration_ms=duration,
                )
                results.append(step_result)
                if isinstance(step_result.data, str):
                    final_text = step_result.data
                elif "text" in step_result.metadata:
                    final_text = str(step_result.metadata["text"])
                self._emit(
                    OcrPipelineStepCompleted(
                        aggregate_id=str(page_number),
                        page_number=page_number,
                        step_name=step_result.step_name,
                        duration_ms=step_result.duration_ms,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - surface as pipeline failure
            total = (time.perf_counter() - started) * 1000.0
            self._emit(
                OcrPipelineFailed(
                    aggregate_id=str(page_number),
                    page_number=page_number,
                    step_name=name,
                    error_message=str(exc),
                )
            )
            logger.error("ocr_pipeline_failed", page_number=page_number, error=str(exc))
            raise

        total = (time.perf_counter() - started) * 1000.0
        self._emit(
            OcrPipelineCompleted(
                aggregate_id=str(page_number),
                page_number=page_number,
                step_count=len(results),
                final_text=final_text,
                duration_ms=total,
            )
        )
        return OcrPipelineResult(
            page_number=page_number,
            step_results=tuple(results),
            final_text=final_text,
            duration_ms=total,
            is_success=True,
        )
