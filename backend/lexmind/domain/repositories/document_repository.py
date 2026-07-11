"""Document repository interface."""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.document import Document
from lexmind.domain.enums.domain_enums import DocumentStatus
from lexmind.domain.repositories.base_repository import BaseRepository


@runtime_checkable
class DocumentRepository(BaseRepository[Document], Protocol):
    """Persistence contract for Document entities.

    Extends BaseRepository with document-specific queries.
    """

    def find_by_workspace(self, workspace_id: str) -> list[Document]:
        """Find all documents in a workspace."""

    def find_by_case(self, case_id: str) -> list[Document]:
        """Find all documents linked to a case."""

    def find_by_hash(self, file_hash: str) -> Document | None:
        """Find a document by its file hash (for duplicate detection)."""

    def find_by_status(self, workspace_id: str, status: DocumentStatus) -> list[Document]:
        """Find documents by processing status within a workspace."""

    def find_duplicates(self, workspace_id: str) -> list[Document]:
        """Find all documents marked as duplicates in a workspace."""
