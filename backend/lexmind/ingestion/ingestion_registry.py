"""Registry of ingestion sources and active jobs."""

from lexmind.ingestion.ingestion_exceptions import JobNotFoundError
from lexmind.ingestion.ingestion_job import IngestionJob
from lexmind.ingestion.ingestion_source import IngestionSource


class IngestionRegistry:
    """Stores registered sources by name and tracks ingestion jobs."""

    def __init__(self) -> None:
        self._sources: dict[str, IngestionSource] = {}
        self._jobs: dict[str, IngestionJob] = {}

    def register_source(self, source: IngestionSource) -> None:
        """Register a source under its ``name``."""
        self._sources[source.name] = source

    def get_source(self, name: str) -> IngestionSource | None:
        """Return the source registered under ``name`` if present."""
        return self._sources.get(name)

    def sources(self) -> list[str]:
        """Return the names of all registered sources."""
        return list(self._sources)

    def add_job(self, job: IngestionJob) -> None:
        """Track an ingestion job by its id."""
        self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> IngestionJob:
        """Return a tracked job or raise ``JobNotFoundError``."""
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(f"No ingestion job with id '{job_id}'.")
        return job

    def jobs(self) -> list[IngestionJob]:
        """Return all tracked jobs."""
        return list(self._jobs.values())
