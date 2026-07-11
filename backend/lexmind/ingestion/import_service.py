"""Import Service -- imports documents via StorageManager and repositories.

Responsibilities:
    - Import single files or folders
    - Detect supported formats
    - Compute checksum
    - Create Document entity
    - Store original file via StorageManager
    - Register metadata via DocumentRepository
    - Publish ImportStarted / ImportCompleted events
    - No direct filesystem access (all I/O via StorageManager)

Flow:
    CLI/API -> ImportService -> StorageManager -> DocumentRepository -> EventBus
"""

from __future__ import annotations

from pathlib import PurePosixPath

from lexmind.domain.entities.document import Document
from lexmind.domain.enums.domain_enums import (
    DocumentStatus,
    DocumentTypeEnum,
    ProcessingStatus,
)
from lexmind.domain.events.domain_events import DocumentImported
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.ingestion.import_events import ImportCompleted, ImportStarted

# Supported file extensions mapped to DocumentTypeEnum.
_FORMAT_MAP: dict[str, DocumentTypeEnum] = {
    ".pdf": DocumentTypeEnum.OTHER,
    ".docx": DocumentTypeEnum.OTHER,
    ".odt": DocumentTypeEnum.OTHER,
    ".txt": DocumentTypeEnum.OTHER,
    ".jpg": DocumentTypeEnum.PHOTOGRAPH,
    ".jpeg": DocumentTypeEnum.PHOTOGRAPH,
    ".png": DocumentTypeEnum.PHOTOGRAPH,
    ".tif": DocumentTypeEnum.PHOTOGRAPH,
    ".tiff": DocumentTypeEnum.PHOTOGRAPH,
}

# MIME type lookup by extension.
_MIME_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


class ImportService:
    """Imports documents into a workspace.

    Uses StorageManager for file persistence, DocumentRepository for
    metadata, and EventBus for event publication.  No direct
    filesystem access is performed.
    """

    def __init__(
        self,
        workspace_id: str,
        storage_manager: object,
        document_repository: object,
        event_bus: object | None = None,
    ) -> None:
        """Initialise with collaborators.

        Args:
            workspace_id: The workspace to import into.
            storage_manager: StorageManager for file persistence.
            document_repository: DocumentRepository for metadata.
            event_bus: Optional event bus for publishing events.
        """
        self._workspace_id = workspace_id
        self._storage = storage_manager
        self._repo = document_repository
        self._event_bus = event_bus

    def import_file(
        self,
        file_path: str,
        file_data: bytes,
        title: str = "",
    ) -> Document:
        """Import a single file into the workspace.

        Args:
            file_path: Original file path (used for name and format detection).
            file_data: Raw file bytes to store.
            title: Optional document title.  Defaults to filename.

        Returns:
            The created Document entity.

        Raises:
            ValueError: If the file format is not supported.
        """
        self._publish(ImportStarted(
            aggregate_id=self._workspace_id,
            workspace_id=self._workspace_id,
            file_path=file_path,
            file_name=PurePosixPath(file_path).name,
        ))

        ext = PurePosixPath(file_path).suffix.lower()
        if ext not in _FORMAT_MAP:
            raise ValueError(f"Unsupported file format: {ext}")

        file_hash = self._compute_hash(file_data)

        existing = self._repo.find_by_hash(file_hash)  # type: ignore[union-attr]
        is_duplicate = existing is not None

        doc_title = title or PurePosixPath(file_path).stem
        doc = Document(
            workspace_id=self._workspace_id,
            title=doc_title,
            file_path=FilePath(value=PurePosixPath(file_path).name),
            file_hash=FileHash(value=file_hash),
            mime_type=_MIME_MAP.get(ext, "application/octet-stream"),
            document_type=_FORMAT_MAP.get(ext, DocumentTypeEnum.OTHER),
            status=DocumentStatus.IMPORTED,
            processing_status=ProcessingStatus.PENDING,
            is_duplicate=is_duplicate,
        )

        storage_uri = self._build_uri(doc.id, PurePosixPath(file_path).name)
        self._storage.save(storage_uri, file_data)  # type: ignore[union-attr]

        self._repo.create(doc)  # type: ignore[union-attr]

        self._publish(DocumentImported(
            aggregate_id=doc.id,
            workspace_id=self._workspace_id,
            file_path=file_path,
            file_hash=file_hash,
        ))
        self._publish(ImportCompleted(
            aggregate_id=doc.id,
            workspace_id=self._workspace_id,
            document_id=doc.id,
            file_path=file_path,
            file_hash=file_hash,
            mime_type=doc.mime_type,
            is_duplicate=is_duplicate,
        ))

        return doc

    def import_folder(
        self,
        folder_path: str,
        files: dict[str, bytes],
    ) -> list[Document]:
        """Import multiple files from a folder.

        Args:
            folder_path: The folder path (for context).
            files: Mapping of relative file paths to their bytes.

        Returns:
            List of created Document entities.
        """
        documents: list[Document] = []
        for rel_path, data in files.items():
            full_path = f"{folder_path}/{rel_path}"
            doc = self.import_file(full_path, data)
            documents.append(doc)
        return documents

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA-1 hex digest (matches FileHash constraint)."""
        import hashlib

        return hashlib.sha1(data).hexdigest()  # noqa: S324

    def _build_uri(self, doc_id: str, filename: str) -> str:
        """Build a storage URI for the original file."""
        return f"storage://{self._workspace_id}/originals/{doc_id}/{filename}"

    def _publish(self, event: object) -> None:
        """Publish an event if the event bus is available."""
        if self._event_bus is not None:
            self._event_bus.publish(event)  # type: ignore[union-attr]
