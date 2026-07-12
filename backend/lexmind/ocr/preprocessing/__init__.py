"""Image preprocessing framework.

A composable, engine-agnostic preprocessing pipeline that prepares images
for OCR (grayscale, deskew, denoise, binarize, resize).  Pixel work is
delegated to an injectable :class:`ImageEngine`; the framework, operations
and pipeline contain no imaging-library imports and are fully unit-testable
with a stub engine.
"""

from __future__ import annotations

from lexmind.ocr.preprocessing.image_engine import ImageEngine
from lexmind.ocr.preprocessing.image_operation import (
    BinarizeOperation,
    DenoiseOperation,
    DeskewOperation,
    GrayscaleOperation,
    ImageOperation,
    ImageOperationError,
    ImageOperationRegistry,
    ResizeOperation,
    build_default_registry,
)
from lexmind.ocr.preprocessing.image_preprocessor import (
    ImagePreprocessingPipeline,
    ImagePreprocessor,
)
from lexmind.ocr.preprocessing.pillow_engine import PillowImageEngine
from lexmind.ocr.preprocessing.preprocessing_events import (
    ImagePreprocessingCompleted,
    ImagePreprocessingFailed,
    ImagePreprocessingStarted,
)
from lexmind.ocr.preprocessing.preprocessing_plugin import ImagePreprocessingPlugin
from lexmind.ocr.preprocessing.preprocessing_types import (
    PreprocessingOptions,
    PreprocessingResult,
)

__all__ = [
    "BinarizeOperation",
    "DenoiseOperation",
    "DeskewOperation",
    "GrayscaleOperation",
    "ImageEngine",
    "ImageOperation",
    "PillowImageEngine",
    "ImageOperationError",
    "ImageOperationRegistry",
    "ImagePreprocessingCompleted",
    "ImagePreprocessingFailed",
    "ImagePreprocessingPipeline",
    "ImagePreprocessingPlugin",
    "ImagePreprocessingStarted",
    "ImagePreprocessor",
    "PreprocessingOptions",
    "PreprocessingResult",
    "ResizeOperation",
    "build_default_registry",
]
