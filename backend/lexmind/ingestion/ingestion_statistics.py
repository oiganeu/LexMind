"""Ingestion statistics model."""

from dataclasses import dataclass


@dataclass
class IngestionStatistics:
    """Aggregated metrics for an ingestion run."""

    total_files: int = 0
    imported: int = 0
    skipped: int = 0
    duplicates: int = 0
    unsupported: int = 0
    errors: int = 0
    duration_seconds: float = 0.0

    @property
    def average_file_time(self) -> float:
        """Average processing time per imported file in seconds."""
        if self.imported <= 0:
            return 0.0
        return self.duration_seconds / self.imported

    def record_imported(self) -> None:
        """Count a successfully imported file."""
        self.imported += 1

    def record_skipped(self) -> None:
        """Count a skipped file."""
        self.skipped += 1

    def record_duplicate(self) -> None:
        """Count a duplicate file."""
        self.duplicates += 1

    def record_unsupported(self) -> None:
        """Count an unsupported file."""
        self.unsupported += 1

    def record_error(self) -> None:
        """Count a file that failed with an error."""
        self.errors += 1
