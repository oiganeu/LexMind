"""OCR pipeline framework.

Runs an ordered, composable sequence of processing steps over a document
image and aggregates their results.  Steps implement the
:class:`~lexmind.ocr.pipeline.pipeline_step.OcrPipelineStep` Protocol and are
resolved by name from an
:class:`~lexmind.ocr.pipeline.pipeline_step.OcrPipelineStepRegistry`.  The
orchestrating :class:`~lexmind.ocr.pipeline.ocr_pipeline.OcrPipelineService`
runs each enabled step in order and emits lifecycle events, while
:class:`~lexmind.ocr.pipeline.ocr_pipeline_plugin.OcrPipelinePlugin` exposes
the framework through the plugin system under
:class:`PluginCapability.OCR_PIPELINE`.
"""

from __future__ import annotations

from lexmind.ocr.pipeline.ocr_pipeline import OcrPipelineService
from lexmind.ocr.pipeline.ocr_pipeline_events import (
    OcrPipelineCompleted,
    OcrPipelineFailed,
    OcrPipelineStarted,
    OcrPipelineStepCompleted,
)
from lexmind.ocr.pipeline.ocr_pipeline_plugin import OcrPipelinePlugin
from lexmind.ocr.pipeline.pipeline_step import (
    IdentityPipelineStep,
    OcrPipelineStep,
    OcrPipelineStepNotFoundError,
    OcrPipelineStepRegistry,
    PipelineContext,
)
from lexmind.ocr.pipeline.pipeline_types import (
    OcrPipelineOptions,
    OcrPipelineResult,
    PipelineStepResult,
)

__all__ = [
    "IdentityPipelineStep",
    "OcrPipelineCompleted",
    "OcrPipelineFailed",
    "OcrPipelineOptions",
    "OcrPipelinePlugin",
    "OcrPipelineResult",
    "OcrPipelineService",
    "OcrPipelineStarted",
    "OcrPipelineStepCompleted",
    "OcrPipelineStep",
    "OcrPipelineStepNotFoundError",
    "OcrPipelineStepRegistry",
    "PipelineContext",
    "PipelineStepResult",
]
