"""OCR provider plugins.

Concrete OCR engine implementations of the
:class:`~lexmind.ocr.ocr_provider.OCRProvider` contract.  Each provider
isolates all engine-specific code; the orchestration layer stays
engine-agnostic.
"""

from lexmind.ocr.providers.ocr_result_mapper import (
    OCRResultMapper,
    TesseractRawOutput,
    TesseractWord,
)
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_provider import (
    PytesseractEngine,
    TesseractEngine,
    TesseractOCRProvider,
)

__all__ = [
    "OCRResultMapper",
    "PytesseractEngine",
    "TesseractConfig",
    "TesseractEngine",
    "TesseractOCRProvider",
    "TesseractRawOutput",
    "TesseractWord",
]
