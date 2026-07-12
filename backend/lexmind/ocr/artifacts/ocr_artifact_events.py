"""Domain events for OCR artifact integration."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.events.event import Event


@dataclass
class OcrArtifactStored(Event):
    """Emitted when an OCR artifact is successfully stored."""

    name: str = "ocr_artifact_stored"
    source_module: str = "ocr_artifacts"
    artifact_id: str = ""
    document_id: str = ""
    page_number: int = 1


@dataclass
class OcrArtifactDeleted(Event):
    """Emitted when an OCR artifact is deleted."""

    name: str = "ocr_artifact_deleted"
    source_module: str = "ocr_artifacts"
    artifact_id: str = ""


@dataclass
class OcrArtifactFailed(Event):
    """Emitted when an OCR artifact operation fails."""

    name: str = "ocr_artifact_failed"
    source_module: str = "ocr_artifacts"
    artifact_id: str = ""
    error_message: str = ""
