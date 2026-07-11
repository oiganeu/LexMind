"""Document version entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.file import FileHash, FilePath


@dataclass
class DocumentVersion(BaseEntity):
    """Immutable version snapshot of a document.

    Versions are append-only.  Each version records the file state
    at a point in time.
    """

    document_id: str = ""
    version_number: int = 0
    file_path: FilePath | None = None
    file_hash: FileHash | None = None
    comment: str = ""
    created_by: str = ""

    def __post_init__(self) -> None:
        if not self.document_id:
            raise InvariantViolationError("DocumentVersion must reference a document")
        if self.version_number < 1:
            raise InvariantViolationError("DocumentVersion number must be >= 1")
