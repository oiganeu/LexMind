# SQLite Metadata Store

Persistent metadata storage for LexMind using SQLAlchemy 2.x.

## Architecture

```
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
```

## Quick Start

```python
from lexmind.metadata import Database, SessionManager, SqliteWorkspaceRepository

db = Database("sqlite:///lexmind.db")
db.initialize()
sm = SessionManager(db.engine)
repo = SqliteWorkspaceRepository(sm)

# Create
ws = Workspace(name="My Workspace", owner_id="user-1")
repo.create(ws)

# Read
loaded = repo.get(ws.id)

# Update
loaded.description = "Updated"
repo.update(loaded)

# Delete
repo.delete(ws.id)
```

## Key Design Decisions

- **No SQLAlchemy in domain layer** -- repositories convert ORM models to domain entities.
- **Context-managed sessions** -- `session_scope()` auto-commits/rollbacks.
- **Tuple serialization** -- `document_ids`, `case_ids`, etc. stored as comma-separated strings.
- **WAL journal mode** -- enabled by default for concurrent reads.
- **Foreign keys enforced** -- SQLite PRAGMA enabled on connect.

## Packages

| Module | Description |
|--------|-------------|
| `database.py` | Engine lifecycle, table creation |
| `session.py` | Session factory with context manager |
| `repositories.py` | CRUD implementations returning domain entities |
| `models.py` | SQLAlchemy ORM table definitions |
| `schema.py` | Pydantic validation schemas |
| `migrations.py` | Version-tracked schema migrations |
| `exceptions.py` | Metadata-specific error hierarchy |
