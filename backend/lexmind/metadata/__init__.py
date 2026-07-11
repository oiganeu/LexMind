"""SQLite Metadata Store.

Provides persistent metadata storage using SQLAlchemy 2.x.
Domain entities are never exposed outside this package;
repositories handle the conversion between ORM models and domain objects.

Quick start::

    from lexmind.metadata import Database, SessionManager, SqliteWorkspaceRepository

    db = Database("sqlite:///lexmind.db")
    db.initialize()
    sm = SessionManager(db.engine)
    repo = SqliteWorkspaceRepository(sm)

Architecture::

    Application / Domain
          |
    Repository Protocol    (domain layer -- no SQLAlchemy)
          |
    SqliteXxxRepository    (this package -- SQLAlchemy)
          |
    SessionManager         (context-managed sessions)
          |
    Database               (engine + table creation)
          |
    SQLite
"""

from lexmind.metadata.database import Database
from lexmind.metadata.exceptions import (
    ConcurrencyError,
    DatabaseConnectionError,
    DatabaseError,
    EntityNotFoundError,
    MetadataError,
    MigrationError,
    MigrationVersionError,
    SchemaValidationError,
    SessionCommitError,
    SessionError,
    SessionRollbackError,
)
from lexmind.metadata.migrations import Migration, MigrationRunner, MigrationTracker
from lexmind.metadata.models import Base, CaseRow, DocumentRow, WorkspaceRow
from lexmind.metadata.repositories import (
    SqliteCaseRepository,
    SqliteDocumentRepository,
    SqliteWorkspaceRepository,
)
from lexmind.metadata.schema import (
    CaseCreate,
    CaseRead,
    CaseUpdate,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from lexmind.metadata.session import SessionManager

__all__ = [
    # Database
    "Database",
    # Session
    "SessionManager",
    # Repositories
    "SqliteCaseRepository",
    "SqliteDocumentRepository",
    "SqliteWorkspaceRepository",
    # Models
    "Base",
    "CaseRow",
    "DocumentRow",
    "WorkspaceRow",
    # Schemas
    "CaseCreate",
    "CaseRead",
    "CaseUpdate",
    "DocumentCreate",
    "DocumentRead",
    "DocumentUpdate",
    "WorkspaceCreate",
    "WorkspaceRead",
    "WorkspaceUpdate",
    # Migrations
    "Migration",
    "MigrationRunner",
    "MigrationTracker",
    # Exceptions
    "ConcurrencyError",
    "DatabaseConnectionError",
    "DatabaseError",
    "EntityNotFoundError",
    "MigrationError",
    "MigrationVersionError",
    "MetadataError",
    "SchemaValidationError",
    "SessionCommitError",
    "SessionError",
    "SessionRollbackError",
]
