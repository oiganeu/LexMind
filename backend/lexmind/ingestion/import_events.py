"""Import pipeline domain events."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class ImportStarted(DomainEvent):
    """Raised when a file import begins."""

    workspace_id: str = ""
    file_path: str = ""
    file_name: str = ""


@dataclass(frozen=True, slots=True)
class ImportCompleted(DomainEvent):
    """Raised when a file import completes successfully."""

    workspace_id: str = ""
    document_id: str = ""
    file_path: str = ""
    file_hash: str = ""
    mime_type: str = ""
    is_duplicate: bool = False
