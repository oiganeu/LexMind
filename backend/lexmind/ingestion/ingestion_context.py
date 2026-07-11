"""Ingestion execution context.

Carries the injected collaborators shared across pipeline stages for a
single job. No global state is used; everything is passed explicitly.
"""

from dataclasses import dataclass, field

from lexmind.ingestion.duplicate_detector import DuplicateDetector
from lexmind.ingestion.ingestion_job import IngestionJob
from lexmind.ingestion.ingestion_result import IngestionResult
from lexmind.ingestion.ingestion_source import IngestionSource
from lexmind.ingestion.ingestion_statistics import IngestionStatistics
from lexmind.ingestion.mime_detector import MimeDetector
from lexmind.ingestion.path_validator import PathValidator


@dataclass
class IngestionContext:
    """Shared state and collaborators for a single ingestion job."""

    job: IngestionJob
    source: IngestionSource
    location: str
    recursive: bool = True
    mime_detector: MimeDetector = field(default_factory=MimeDetector)
    path_validator: PathValidator = field(default_factory=PathValidator)
    duplicate_detector: DuplicateDetector = field(default_factory=DuplicateDetector)
    statistics: IngestionStatistics = field(default_factory=IngestionStatistics)
    result: IngestionResult = field(init=False)

    def __post_init__(self) -> None:
        self.result = IngestionResult(job_id=self.job.job_id)
