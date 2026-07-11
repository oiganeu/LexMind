"""Database engine and table initialisation.

Owns the SQLAlchemy ``Engine`` and ``MetaData``.  All other modules
receive the engine via dependency injection -- no global engine.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, event

from lexmind.metadata.exceptions import DatabaseConnectionError
from lexmind.metadata.models import Base


class Database:
    """Manages the SQLAlchemy engine and schema lifecycle.

    Usage::

        db = Database("sqlite:///data/lexmind.db")
        db.initialize()
        ...

    Constraints:
        - No global engine; the instance owns its engine.
        - WAL journal mode enabled by default for concurrency.
        - Foreign keys enforced.
    """

    def __init__(self, url: str = "sqlite:///:memory:") -> None:
        """Initialise with a database URL.

        Args:
            url: SQLAlchemy connection URL.  Defaults to in-memory.
        """
        self._url = url
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        """Return the SQLAlchemy engine.

        Raises DatabaseConnectionError if not yet initialised.
        """
        if self._engine is None:
            raise DatabaseConnectionError(self._url, "call initialize() first")
        return self._engine

    def initialize(self) -> Engine:
        """Create the engine and all tables.

        Returns:
            The initialised SQLAlchemy Engine.
        """
        self._engine = create_engine(
            self._url,
            echo=False,
            future=True,
        )
        self._configure(self._engine)
        Base.metadata.create_all(self._engine)
        return self._engine

    def dispose(self) -> None:
        """Dispose the engine and release all connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    @staticmethod
    def _configure(engine: Engine) -> None:
        """Apply SQLite-specific pragmas via connection events."""
        if engine.url.get_backend_name() != "sqlite":
            return

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(
            dbapi_conn: object, connection_record: object  # noqa: ARG001
        ) -> None:
            cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    @property
    def url(self) -> str:
        """Return the database URL."""
        return self._url

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"Database(url={self._url!r})"
