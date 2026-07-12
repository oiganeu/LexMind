"""OCR artifact subpackage.

Generates, persists and registers standardised OCR artifacts
independently of any OCR engine.  The integration layer associates OCR
output with document artifacts such as pages, images and regions.
"""

from lexmind.ocr.artifacts.artifact_repository import (
    ArtifactRepository,
    ArtifactRepositoryNotFoundError,
    ArtifactRepositoryRegistry,
    DuplicateArtifactError,
    InMemoryArtifactRepository,
)
from lexmind.ocr.artifacts.artifact_types import (
    OcrArtifact,
    OcrArtifactOptions,
    OcrArtifactQuery,
)
from lexmind.ocr.artifacts.ocr_artifact_events import (
    OcrArtifactDeleted,
    OcrArtifactFailed,
    OcrArtifactStored,
)
from lexmind.ocr.artifacts.ocr_artifact_generator import (
    JSON_MEDIA_TYPE,
    METADATA_FILENAME,
    RESULT_FILENAME,
    TEXT_FILENAME,
    TEXT_MEDIA_TYPE,
    OCRArtifactGenerator,
    OCRArtifactSet,
)
from lexmind.ocr.artifacts.ocr_artifact_integration import (
    OcrArtifactIntegrationService,
)
from lexmind.ocr.artifacts.ocr_artifact_plugin import OcrArtifactIntegrationPlugin
from lexmind.ocr.artifacts.ocr_artifact_repository_adapter import (
    OCRArtifactRepositoryAdapter,
)
from lexmind.ocr.artifacts.ocr_artifact_serializer import OCRArtifactSerializer

__all__ = [
    "ArtifactRepository",
    "ArtifactRepositoryNotFoundError",
    "ArtifactRepositoryRegistry",
    "DuplicateArtifactError",
    "InMemoryArtifactRepository",
    "JSON_MEDIA_TYPE",
    "METADATA_FILENAME",
    "OcrArtifact",
    "OcrArtifactDeleted",
    "OcrArtifactFailed",
    "OcrArtifactIntegrationPlugin",
    "OcrArtifactIntegrationService",
    "OcrArtifactOptions",
    "OcrArtifactQuery",
    "OcrArtifactStored",
    "OCRArtifactGenerator",
    "OCRArtifactRepositoryAdapter",
    "OCRArtifactSerializer",
    "OCRArtifactSet",
    "RESULT_FILENAME",
    "TEXT_FILENAME",
    "TEXT_MEDIA_TYPE",
]
