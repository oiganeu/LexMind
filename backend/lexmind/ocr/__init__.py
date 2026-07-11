"""OCR orchestration layer.

Coordinates OCR recognition without embedding any engine-specific
logic.  Concrete engines (Tesseract, PaddleOCR, cloud OCR) are provided
as plugins implementing :class:`OCRProvider`.

Public API:
    - OCRPipeline: end-to-end orchestrator
    - OCRRequest / OCROutcome: pipeline input and output
    - OCRDispatcher: provider selection registry
    - OCRProvider: provider plugin interface
    - OCRArtifactWriter: persists results via StorageManager
    - OCRResult / OCRPageResult: recognition result value objects
    - OCRStarted / OCRCompleted / OCRFailed: lifecycle events
"""

from lexmind.ocr.ocr_artifact_writer import OCRArtifactWriter
from lexmind.ocr.ocr_dispatcher import OCRDispatcher, OCRProviderNotFoundError
from lexmind.ocr.ocr_events import OCRCompleted, OCRFailed, OCRStarted
from lexmind.ocr.ocr_pipeline import OCROutcome, OCRPipeline, OCRRequest
from lexmind.ocr.ocr_provider import OCRProvider
from lexmind.ocr.ocr_result import OCRPageResult, OCRResult

__all__ = [
    "OCRArtifactWriter",
    "OCRCompleted",
    "OCRDispatcher",
    "OCRFailed",
    "OCROutcome",
    "OCRPageResult",
    "OCRPipeline",
    "OCRProvider",
    "OCRProviderNotFoundError",
    "OCRRequest",
    "OCRResult",
    "OCRStarted",
]
