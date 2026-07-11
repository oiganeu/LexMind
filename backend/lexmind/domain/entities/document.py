"""Document entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.enums.domain_enums import DocumentStatus, DocumentTypeEnum, ProcessingStatus
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.domain.value_objects.language import Language


@dataclass
class Document(BaseEntity):
    """Document — the central entity in the LexMind domain.

    A document belongs to one workspace and may appear in many cases.
    It progresses through import and processing statuses.
    """

    workspace_id: str = ""
    title: str = ""
    file_path: FilePath | None = None
    file_hash: FileHash | None = None
    mime_type: str = ""
    document_type: DocumentTypeEnum = DocumentTypeEnum.OTHER
    status: DocumentStatus = DocumentStatus.DRAFT
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    language: Language | None = None
    case_ids: tuple[str, ...] = ()
    tag_names: tuple[str, ...] = ()
    version_count: int = 0
    is_duplicate: bool = False
    has_ocr: bool = False
    has_embeddings: bool = False

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise InvariantViolationError("Document must belong to a workspace")

    def link_to_case(self, case_id: str) -> None:
        """Associate this document with a case."""
        if case_id not in self.case_ids:
            self.case_ids = (*self.case_ids, case_id)
            self.touch()

    def unlink_from_case(self, case_id: str) -> None:
        """Remove association with a case."""
        self.case_ids = tuple(c for c in self.case_ids if c != case_id)
        self.touch()

    def mark_imported(self) -> None:
        """Transition to IMPORTED status."""
        self.status = DocumentStatus.IMPORTED
        self.touch()

    def mark_processing(self) -> None:
        """Transition to PROCESSING status."""
        self.status = DocumentStatus.PROCESSING
        self.touch()

    def mark_processed(self) -> None:
        """Transition to PROCESSED status."""
        self.status = DocumentStatus.PROCESSED
        self.processing_status = ProcessingStatus.COMPLETED
        self.touch()

    def mark_failed(self) -> None:
        """Transition to FAILED status."""
        self.status = DocumentStatus.FAILED
        self.touch()

    def increment_version(self) -> int:
        """Record a new version and return the new count."""
        self.version_count += 1
        self.touch()
        return self.version_count

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document."""
        normalized = tag.strip().lower()
        if normalized and normalized not in self.tag_names:
            self.tag_names = (*self.tag_names, normalized)
            self.touch()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document."""
        normalized = tag.strip().lower()
        self.tag_names = tuple(t for t in self.tag_names if t != normalized)
        self.touch()
