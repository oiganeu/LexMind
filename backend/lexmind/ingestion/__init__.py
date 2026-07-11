"""Document ingestion engine framework.

Discovers files, identifies formats, tracks import jobs, detects
duplicates, and dispatches the next processing stages via events. This
package contains only the framework: no OCR, parsing, embedding, or
indexing is performed here.
"""

from lexmind.ingestion.duplicate_detector import DuplicateDetector
from lexmind.ingestion.file_discovery import FileDiscovery
from lexmind.ingestion.ingestion_context import IngestionContext
from lexmind.ingestion.ingestion_exceptions import (
    DiscoveryError,
    DuplicateFileError,
    IngestionError,
    InvalidJobStateError,
    InvalidPathError,
    JobNotFoundError,
    UnsupportedFileTypeError,
)
from lexmind.ingestion.ingestion_job import IngestionJob, JobState, can_transition
from lexmind.ingestion.ingestion_manager import IngestionManager
from lexmind.ingestion.ingestion_pipeline import IngestionPipeline
from lexmind.ingestion.ingestion_registry import IngestionRegistry
from lexmind.ingestion.ingestion_result import (
    DiscoveredFile,
    FileOutcome,
    FileResult,
    IngestionResult,
)
from lexmind.ingestion.ingestion_session import IngestionSession
from lexmind.ingestion.ingestion_source import IngestionSource
from lexmind.ingestion.ingestion_statistics import IngestionStatistics
from lexmind.ingestion.mime_detector import FileCategory, MimeDetector
from lexmind.ingestion.path_validator import PathValidator

__all__ = [
    "DiscoveredFile",
    "DiscoveryError",
    "DuplicateDetector",
    "DuplicateFileError",
    "FileCategory",
    "FileDiscovery",
    "FileOutcome",
    "FileResult",
    "IngestionContext",
    "IngestionError",
    "IngestionJob",
    "IngestionManager",
    "IngestionPipeline",
    "IngestionRegistry",
    "IngestionResult",
    "IngestionSession",
    "IngestionSource",
    "IngestionStatistics",
    "InvalidJobStateError",
    "InvalidPathError",
    "JobNotFoundError",
    "JobState",
    "MimeDetector",
    "PathValidator",
    "UnsupportedFileTypeError",
    "can_transition",
]
