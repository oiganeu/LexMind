"""OCR pipeline domain events."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class OCRStarted(DomainEvent):
    """Raised when an OCR run begins."""

    workspace_id: str = ""
    document_id: str = ""
    provider: str = ""


@dataclass(frozen=True, slots=True)
class OCRCompleted(DomainEvent):
    """Raised when an OCR run completes successfully."""

    workspace_id: str = ""
    document_id: str = ""
    provider: str = ""
    artifact_uri: str = ""
    page_count: int = 0
    confidence: float = 0.0


@dataclass(frozen=True, slots=True)
class OCRFailed(DomainEvent):
    """Raised when an OCR run fails."""

    workspace_id: str = ""
    document_id: str = ""
    provider: str = ""
    error_message: str = ""
