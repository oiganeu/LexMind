"""Ingestion pipeline skeleton.

Executes the framework stages for a job:

    Discover -> Validate -> Identify Type -> Calculate Checksum ->
    Register (duplicate check) -> Publish Events -> Ready for OCR

No OCR, parsing, embedding, or indexing is performed here. Files that pass
all stages are marked as imported and are ready to be handed to the next
processing stage.
"""

from collections.abc import Callable
from typing import Any

from lexmind.ingestion import ingestion_events as events
from lexmind.ingestion.checksum import sha256_file
from lexmind.ingestion.ingestion_context import IngestionContext
from lexmind.ingestion.ingestion_exceptions import InvalidPathError
from lexmind.ingestion.ingestion_job import JobState
from lexmind.ingestion.ingestion_result import (
    DiscoveredFile,
    FileOutcome,
    FileResult,
    IngestionResult,
)

Emitter = Callable[[str, dict[str, Any]], None]


def _noop_emit(name: str, payload: dict[str, Any]) -> None:
    return None


class IngestionPipeline:
    """Runs discovered files through the ingestion framework stages."""

    def __init__(self, emit: Emitter | None = None) -> None:
        self._emit = emit or _noop_emit

    def process(self, context: IngestionContext) -> IngestionResult:
        """Discover and process all files for the given context."""
        job = context.job
        self._emit(events.IMPORT_STARTED, {"job_id": job.job_id, "source": context.source.name})
        job.transition_to(JobState.DISCOVERING)

        discovered = self._discover(context)
        context.statistics.total_files = len(discovered)

        job.transition_to(JobState.VALIDATING)
        job.transition_to(JobState.IMPORTING)

        for index, file in enumerate(discovered, start=1):
            if job.state == JobState.CANCELLED:
                break
            self._process_file(context, file)
            job.files_processed += 1
            job.progress = index / len(discovered) if discovered else 1.0
            self._emit(
                events.IMPORT_PROGRESS,
                {"job_id": job.job_id, "progress": job.progress},
            )

        if not job.is_terminal:
            job.transition_to(JobState.COMPLETED)
        self._emit(events.IMPORT_COMPLETED, {"job_id": job.job_id})
        return context.result

    def _discover(self, context: IngestionContext) -> list[DiscoveredFile]:
        discovered: list[DiscoveredFile] = []
        for file in context.source.discover(context.location, context.recursive):
            discovered.append(file)
            self._emit(
                events.FILE_DISCOVERED,
                {"job_id": context.job.job_id, "path": str(file.path)},
            )
        return discovered

    def _process_file(self, context: IngestionContext, file: DiscoveredFile) -> None:
        job = context.job
        stats = context.statistics

        try:
            context.path_validator.validate(file.path)
        except InvalidPathError as exc:
            stats.record_error()
            job.files_failed += 1
            context.result.add(
                FileResult(path=file.path, outcome=FileOutcome.REJECTED, message=str(exc))
            )
            self._emit(events.FILE_REJECTED, {"path": str(file.path), "reason": str(exc)})
            return

        self._emit(events.FILE_VALIDATED, {"path": str(file.path)})

        if not context.mime_detector.is_supported(file.path):
            stats.record_unsupported()
            context.result.add(
                FileResult(
                    path=file.path,
                    outcome=FileOutcome.UNSUPPORTED,
                    mime_type=file.mime_type,
                    message="Unsupported file type.",
                )
            )
            return

        checksum = sha256_file(file.path)
        if context.duplicate_detector.check_and_register(checksum):
            stats.record_duplicate()
            context.result.add(
                FileResult(
                    path=file.path,
                    outcome=FileOutcome.DUPLICATE,
                    checksum=checksum,
                    mime_type=file.mime_type,
                )
            )
            self._emit(events.DUPLICATE_DETECTED, {"path": str(file.path), "checksum": checksum})
            return

        stats.record_imported()
        context.result.add(
            FileResult(
                path=file.path,
                outcome=FileOutcome.IMPORTED,
                checksum=checksum,
                mime_type=file.mime_type,
            )
        )
