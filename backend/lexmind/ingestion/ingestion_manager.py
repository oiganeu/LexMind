"""Ingestion manager.

Coordinates the ingestion framework: creates jobs, wires collaborators,
runs the pipeline, measures duration, publishes events, and supports
cancellation. This is the single entry point for triggering imports.
"""

import time
from typing import Any

from lexmind.events.event import Event
from lexmind.events.event_bus import EventBus
from lexmind.ingestion import ingestion_events as events
from lexmind.ingestion.duplicate_detector import DuplicateDetector
from lexmind.ingestion.file_discovery import FileDiscovery
from lexmind.ingestion.ingestion_context import IngestionContext
from lexmind.ingestion.ingestion_exceptions import IngestionError
from lexmind.ingestion.ingestion_job import IngestionJob, JobState
from lexmind.ingestion.ingestion_pipeline import IngestionPipeline
from lexmind.ingestion.ingestion_registry import IngestionRegistry
from lexmind.ingestion.ingestion_result import IngestionResult
from lexmind.ingestion.ingestion_source import IngestionSource
from lexmind.ingestion.mime_detector import MimeDetector
from lexmind.ingestion.path_validator import PathValidator


class IngestionManager:
    """Creates and runs ingestion jobs across registered sources."""

    def __init__(
        self,
        registry: IngestionRegistry | None = None,
        event_bus: EventBus | None = None,
        path_validator: PathValidator | None = None,
    ) -> None:
        self._registry = registry or IngestionRegistry()
        self._event_bus = event_bus
        self._path_validator = path_validator or PathValidator()
        if self._registry.get_source(FileDiscovery.name) is None:
            self._registry.register_source(FileDiscovery())

    @property
    def registry(self) -> IngestionRegistry:
        return self._registry

    def register_source(self, source: IngestionSource) -> None:
        """Register an additional ingestion source."""
        self._registry.register_source(source)

    def create_job(self, workspace_id: str, source: str, location: str) -> IngestionJob:
        """Create and track a new ingestion job."""
        if self._registry.get_source(source) is None:
            raise IngestionError(f"No ingestion source registered as '{source}'.")
        job = IngestionJob(workspace_id=workspace_id, source=location)
        self._registry.add_job(job)
        return job

    def run(
        self,
        job: IngestionJob,
        location: str,
        source: str = FileDiscovery.name,
        recursive: bool = True,
    ) -> IngestionResult:
        """Execute the ingestion pipeline for a job."""
        ingestion_source = self._registry.get_source(source)
        if ingestion_source is None:
            raise IngestionError(f"No ingestion source registered as '{source}'.")

        context = IngestionContext(
            job=job,
            source=ingestion_source,
            location=location,
            recursive=recursive,
            mime_detector=MimeDetector(),
            path_validator=self._path_validator,
            duplicate_detector=DuplicateDetector(),
        )
        pipeline = IngestionPipeline(emit=self._emit)
        started = time.perf_counter()
        try:
            result = pipeline.process(context)
        except Exception as exc:  # noqa: BLE001 - surface as ingestion failure
            job.add_warning(str(exc))
            if not job.is_terminal:
                job.transition_to(JobState.FAILED)
            self._emit(events.IMPORT_FAILED, {"job_id": job.job_id, "error": str(exc)})
            raise IngestionError(str(exc)) from exc
        finally:
            context.statistics.duration_seconds = time.perf_counter() - started
        return result

    def cancel_job(self, job_id: str) -> None:
        """Request cancellation of a tracked job."""
        job = self._registry.get_job(job_id)
        if not job.is_terminal:
            job.transition_to(JobState.CANCELLED)

    def get_job(self, job_id: str) -> IngestionJob:
        """Return a tracked job by id."""
        return self._registry.get_job(job_id)

    def _emit(self, name: str, payload: dict[str, Any]) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(Event(name=name, source_module="ingestion", payload=payload))
