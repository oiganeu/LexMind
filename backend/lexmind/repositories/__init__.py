"""Repository interfaces and implementations.

This package provides repository implementations that bridge the
domain layer with persistence.  Each repository returns domain
entities only -- no ORM models leak outside this boundary.
"""

from lexmind.repositories.artifact_repository import (
    ArtifactRepository,
    SqliteArtifactRepositoryImpl,
)
from lexmind.repositories.document_repository import (
    DocumentRepository,
    SqliteDocumentRepositoryImpl,
)
from lexmind.repositories.workspace_repository import (
    SqliteWorkspaceRepositoryImpl,
    WorkspaceRepository,
)

__all__ = [
    "ArtifactRepository",
    "DocumentRepository",
    "SqliteArtifactRepositoryImpl",
    "SqliteDocumentRepositoryImpl",
    "SqliteWorkspaceRepositoryImpl",
    "WorkspaceRepository",
]
