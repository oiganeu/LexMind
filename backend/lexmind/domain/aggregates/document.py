"""Document aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.document import Document
from lexmind.domain.entities.document_version import DocumentVersion
from lexmind.domain.enums.domain_enums import DocumentStatus
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.domain.value_objects.language import Language


@dataclass
class DocumentAggregate:
    """Document aggregate root.

    Manages a document and its version history, enforcing
    version append-only invariant and status transitions.
    """

    document: Document = field(default_factory=Document)
    _versions: tuple[DocumentVersion, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Return the document ID."""
        return self.document.id

    @property
    def title(self) -> str:
        """Return the document title."""
        return self.document.title

    @property
    def status(self) -> DocumentStatus:
        """Return the document status."""
        return self.document.status

    @property
    def version_count(self) -> int:
        """Return the number of versions."""
        return len(self._versions)

    @property
    def latest_version(self) -> DocumentVersion | None:
        """Return the latest version, or None."""
        return self._versions[-1] if self._versions else None

    def import_document(
        self,
        file_path: FilePath,
        file_hash: FileHash,
        mime_type: str,
        language: Language | None = None,
    ) -> None:
        """Import a document for the first time.

        Raises:
            InvariantViolationError: If the document is already imported.
        """
        if self.document.status not in (
            DocumentStatus.DRAFT,
            DocumentStatus.PENDING_IMPORT,
        ):
            raise InvariantViolationError(
                f"Cannot import document in status '{self.document.status.value}'"
            )
        self.document.file_path = file_path
        self.document.file_hash = file_hash
        self.document.mime_type = mime_type
        self.document.language = language
        self.document.mark_imported()
        self._add_version(file_path, file_hash, "Initial import")

    def add_version(
        self,
        file_path: FilePath,
        file_hash: FileHash,
        comment: str = "",
        created_by: str = "",
    ) -> DocumentVersion:
        """Add a new version (append-only).

        Returns:
            The newly created DocumentVersion.

        Raises:
            InvariantViolationError: If the document is not yet imported.
        """
        if self.document.status == DocumentStatus.DRAFT:
            raise InvariantViolationError("Cannot version a draft document")
        return self._add_version(file_path, file_hash, comment, created_by)

    def _add_version(
        self,
        file_path: FilePath,
        file_hash: FileHash,
        comment: str = "",
        created_by: str = "",
    ) -> DocumentVersion:
        version_number = self.document.increment_version()
        version = DocumentVersion(
            document_id=self.document.id,
            version_number=version_number,
            file_path=file_path,
            file_hash=file_hash,
            comment=comment,
            created_by=created_by,
        )
        self._versions = (*self._versions, version)
        return version

    def mark_processing(self) -> None:
        """Begin processing."""
        self.document.mark_processing()

    def mark_processed(self) -> None:
        """Mark processing as complete."""
        self.document.mark_processed()

    def mark_failed(self) -> None:
        """Mark processing as failed."""
        self.document.mark_failed()

    def mark_duplicate(self) -> None:
        """Mark the document as a duplicate."""
        self.document.is_duplicate = True
        self.document.touch()

    def mark_ocr_complete(self) -> None:
        """Record that OCR has been completed."""
        self.document.has_ocr = True
        self.document.touch()

    def mark_embeddings_ready(self) -> None:
        """Record that embeddings have been generated."""
        self.document.has_embeddings = True
        self.document.touch()
