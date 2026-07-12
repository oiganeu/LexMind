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
from lexmind.ocr.providers.paddle_plugin import PaddleOCRPlugin
from lexmind.ocr.providers.paddleocr_provider import (
    DefaultPaddleEngine,
    PaddleOCRConfig,
    PaddleOCREngine,
    PaddleOCRProvider,
    PaddleOCRRawOutput,
    PaddleOCRResultMapper,
    PaddleOCRWord,
)
from lexmind.ocr.providers.plugin import OCRProviderPlugin
from lexmind.ocr.providers.tesseract_config import TesseractConfig
from lexmind.ocr.providers.tesseract_plugin import TesseractPlugin
from lexmind.ocr.providers.tesseract_provider import (
    PytesseractEngine,
    TesseractEngine,
    TesseractOCRProvider,
)

__all__ = [
    "DefaultPaddleEngine",
    "OCRProviderPlugin",
    "OCRResultMapper",
    "PaddleOCREngine",
    "PaddleOCRConfig",
    "PaddleOCRPlugin",
    "PaddleOCRProvider",
    "PaddleOCRRawOutput",
    "PaddleOCRResultMapper",
    "PaddleOCRWord",
    "PytesseractEngine",
    "TesseractConfig",
    "TesseractEngine",
    "TesseractOCRProvider",
    "TesseractPlugin",
    "TesseractRawOutput",
    "TesseractWord",
]
