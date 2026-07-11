"""Lightweight migration framework for schema versioning.

Tracks the applied schema version in a ``schema_versions`` table.
Migrations are plain callables that receive an SQLAlchemy ``Engine``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import text

from lexmind.metadata.exceptions import MigrationError, MigrationVersionError


@dataclass
class Migration:
    """A single database migration.

    Attributes:
        version: Monotonic version string (e.g. "001").
        description: Human-readable migration name.
        up: Callable that applies the migration.
        down: Callable that reverses the migration (optional).
    """

    version: str
    up: Callable[[object], None]
    description: str = ""
    down: Callable[[object], None] | None = None


@dataclass
class MigrationRecord:
    """Record of an applied migration."""

    version: str
    description: str
    applied_at: datetime


class MigrationTracker:
    """Tracks applied migrations in a dedicated table.

    The ``schema_versions`` table stores one row per applied migration.
    """

    def __init__(self, engine: object) -> None:
        """Initialise with a SQLAlchemy engine."""
        self._engine = engine
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create the schema_versions table if it does not exist."""
        stmt = text(
            "CREATE TABLE IF NOT EXISTS schema_versions ("
            "  version TEXT PRIMARY KEY,"
            "  description TEXT NOT NULL DEFAULT '',"
            "  applied_at TEXT NOT NULL"
            ")"
        )
        with self._engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(stmt)
            conn.commit()

    def applied_versions(self) -> list[str]:
        """Return ordered list of applied version strings."""
        stmt = text("SELECT version FROM schema_versions ORDER BY version")
        with self._engine.connect() as conn:  # type: ignore[union-attr]
            result = conn.execute(stmt)
            return [row[0] for row in result]

    def record_applied(self, version: str, description: str = "") -> None:
        """Record that a migration was applied."""
        now = datetime.now(UTC).isoformat()
        stmt = text(
            "INSERT INTO schema_versions (version, description, applied_at) "
            "VALUES (:version, :desc, :applied_at)"
        )
        with self._engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(
                stmt, {"version": version, "desc": description, "applied_at": now}
            )
            conn.commit()

    def remove_record(self, version: str) -> None:
        """Remove a migration record (for rollback)."""
        stmt = text("DELETE FROM schema_versions WHERE version = :version")
        with self._engine.connect() as conn:  # type: ignore[union-attr]
            conn.execute(stmt, {"version": version})
            conn.commit()

    def is_applied(self, version: str) -> bool:
        """Return True if the given version has been applied."""
        return version in self.applied_versions()


class MigrationRunner:
    """Runs migrations in order, tracking state.

    Usage::

        runner = MigrationRunner(engine)
        runner.add(Migration(version="001", description="init", up=create_tables))
        runner.migrate_up()
    """

    def __init__(self, engine: object) -> None:
        """Initialise with a SQLAlchemy engine."""
        self._engine = engine
        self._tracker = MigrationTracker(engine)
        self._migrations: list[Migration] = []

    def add(self, migration: Migration) -> None:
        """Register a migration."""
        self._migrations.append(migration)

    def pending(self) -> list[Migration]:
        """Return migrations that have not yet been applied."""
        applied = set(self._tracker.applied_versions())
        return [m for m in self._migrations if m.version not in applied]

    def migrate_up(self) -> list[str]:
        """Apply all pending migrations in order.

        Returns:
            List of applied version strings.

        Raises:
            MigrationError: If a migration fails.
        """
        applied: list[str] = []
        for migration in self.pending():
            try:
                migration.up(self._engine)
                self._tracker.record_applied(
                    migration.version, migration.description
                )
                applied.append(migration.version)
            except Exception as exc:
                raise MigrationError(
                    f"Migration {migration.version} failed: {exc}"
                ) from exc
        return applied

    def migrate_down(self, version: str) -> list[str]:
        """Roll back migrations down to (and including) *version*.

        Returns:
            List of rolled-back version strings.

        Raises:
            MigrationVersionError: If version is not in applied set.
            MigrationError: If a rollback migration fails.
        """
        applied = self._tracker.applied_versions()
        if version not in applied:
            raise MigrationVersionError(version, "not applied")

        rolled_back: list[str] = []
        for migration in reversed(self._migrations):
            if migration.version not in applied:
                continue
            if migration.down is None:
                raise MigrationError(
                    f"Migration {migration.version} has no rollback"
                )
            try:
                migration.down(self._engine)
                self._tracker.remove_record(migration.version)
                rolled_back.append(migration.version)
            except Exception as exc:
                raise MigrationError(
                    f"Rollback {migration.version} failed: {exc}"
                ) from exc
            if migration.version == version:
                break
        return rolled_back

    def current_version(self) -> str | None:
        """Return the latest applied version, or None."""
        versions = self._tracker.applied_versions()
        return versions[-1] if versions else None
