"""OCR artifact generation subpackage.

Generates, persists and registers standardised OCR artifacts
(``ocr_text.txt``, ``ocr_result.json``, ``ocr_metadata.json``)
independently of any OCR engine.
"""

from lexmind.ocr.artifacts.ocr_artifact_generator import (
    JSON_MEDIA_TYPE,
    METADATA_FILENAME,
    RESULT_FILENAME,
    TEXT_FILENAME,
    TEXT_MEDIA_TYPE,
    OCRArtifactGenerator,
    OCRArtifactSet,
)
from lexmind.ocr.artifacts.ocr_artifact_repository_adapter import (
    OCRArtifactRepositoryAdapter,
)
from lexmind.ocr.artifacts.ocr_artifact_serializer import OCRArtifactSerializer

__all__ = [
    "JSON_MEDIA_TYPE",
    "METADATA_FILENAME",
    "RESULT_FILENAME",
    "TEXT_FILENAME",
    "TEXT_MEDIA_TYPE",
    "OCRArtifactGenerator",
    "OCRArtifactRepositoryAdapter",
    "OCRArtifactSerializer",
    "OCRArtifactSet",
]
