"""OCR pipeline orchestrator.

Coordinates the OCR workflow: selects a provider, loads the input
artifact from storage, executes recognition, persists the output, and
publishes lifecycle events.  Contains no engine-specific logic -- all
recognition is delegated to the selected :class:`OCRProvider`.

Flow::

    JobExecutor -> OCRPipeline.execute()
        -> OCRDispatcher.select()
        -> StorageManager.load()      (prepare input)
        -> OCRProvider.recognize()
        -> OCRArtifactWriter.write()  (persist output)
        -> EventBus (OCRStarted / OCRCompleted / OCRFailed)
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from lexmind.ocr.ocr_artifact_writer import OCRArtifactWriter
from lexmind.ocr.ocr_dispatcher import OCRDispatcher
from lexmind.ocr.ocr_events import OCRCompleted, OCRFailed, OCRStarted
from lexmind.ocr.ocr_result import OCRResult

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OCRRequest:
    """A request to run OCR on a stored document."""

    workspace_id: str
    document_id: str
    source_uri: str
    language: str = ""
    mime_type: str = ""
    provider: str | None = None

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.document_id:
            raise ValueError("document_id is required")
        if not self.source_uri:
            raise ValueError("source_uri is required")


@dataclass(frozen=True, slots=True)
class OCROutcome:
    """The result of an OCR pipeline run."""

    result: OCRResult
    artifact_uri: str
    provider: str


class OCRPipeline:
    """Orchestrates OCR recognition end to end."""

    def __init__(
        self,
        dispatcher: OCRDispatcher,
        artifact_writer: OCRArtifactWriter,
        storage_manager: object,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with injected collaborators.

        Args:
            dispatcher: Selects the OCR provider.
            artifact_writer: Persists the OCR output.
            storage_manager: Loads the input artifact.
            event_bus: Optional event bus for lifecycle events.
        """
        self._dispatcher = dispatcher
        self._writer = artifact_writer
        self._storage = storage_manager
        self._event_bus = event_bus

    def execute(self, request: OCRRequest) -> OCROutcome:
        """Run the OCR pipeline for *request*.

        Args:
            request: The OCR request describing the input document.

        Returns:
            An :class:`OCROutcome` with the result and artifact URI.

        Raises:
            Exception: Re-raises any error after publishing OCRFailed.
        """
        provider_name = request.provider or ""
        try:
            provider = self._dispatcher.select(
                name=request.provider,
                mime_type=request.mime_type,
            )
            provider_name = provider.name

            self._emit(OCRStarted(
                aggregate_id=request.document_id,
                workspace_id=request.workspace_id,
                document_id=request.document_id,
                provider=provider_name,
            ))

            image_data = self._storage.load(request.source_uri)  # type: ignore[union-attr]

            result = provider.recognize(
                image_data,
                language=request.language,
                mime_type=request.mime_type,
            )

            artifact_uri = self._writer.write(
                request.workspace_id,
                request.document_id,
                result,
            )

            self._emit(OCRCompleted(
                aggregate_id=request.document_id,
                workspace_id=request.workspace_id,
                document_id=request.document_id,
                provider=provider_name,
                artifact_uri=artifact_uri,
                page_count=result.page_count,
                confidence=result.confidence,
            ))
            logger.info(
                "ocr_completed",
                document_id=request.document_id,
                provider=provider_name,
                artifact_uri=artifact_uri,
            )
            return OCROutcome(
                result=result,
                artifact_uri=artifact_uri,
                provider=provider_name,
            )
        except Exception as exc:
            self._emit(OCRFailed(
                aggregate_id=request.document_id,
                workspace_id=request.workspace_id,
                document_id=request.document_id,
                provider=provider_name,
                error_message=str(exc),
            ))
            logger.error(
                "ocr_failed",
                document_id=request.document_id,
                provider=provider_name,
                error=str(exc),
            )
            raise

    def _emit(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "OCRPipeline()"
