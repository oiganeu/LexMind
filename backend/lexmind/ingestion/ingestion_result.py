"""Ingestion result models."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from lexmind.ingestion.mime_detector import FileCategory


class FileOutcome(StrEnum):
    """Outcome of processing a single discovered file."""

    IMPORTED = "imported"
    DUPLICATE = "duplicate"
    UNSUPPORTED = "unsupported"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class DiscoveredFile:
    """A file located during discovery, before processing."""

    path: Path
    size_bytes: int
    mime_type: str
    category: FileCategory


@dataclass
class FileResult:
    """The result of processing one file."""

    path: Path
    outcome: FileOutcome
    checksum: str | None = None
    mime_type: str | None = None
    message: str | None = None


@dataclass
class IngestionResult:
    """The aggregate result of an ingestion job."""

    job_id: str
    files: list[FileResult] = field(default_factory=list)

    def add(self, result: FileResult) -> None:
        """Append a file result."""
        self.files.append(result)

    def count(self, outcome: FileOutcome) -> int:
        """Return the number of files with the given outcome."""
        return sum(1 for result in self.files if result.outcome == outcome)
