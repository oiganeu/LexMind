"""Context-managed session factory.

Provides ``session_scope()`` for transactional access.  All
repositories receive a session via dependency injection.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, sessionmaker

from lexmind.metadata.exceptions import (
    SessionRollbackError,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SessionManager:
    """Factory for context-managed SQLAlchemy sessions.

    Usage::

        mgr = SessionManager(engine)
        with mgr.session_scope() as session:
            session.add(...)

    The session is automatically committed on clean exit
    and rolled back on exception.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialise with a SQLAlchemy engine.

        Args:
            engine: An initialised SQLAlchemy Engine.
        """
        self._factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            future=True,
        )

    @contextmanager
    def session_scope(self) -> Generator[Session]:
        """Provide a transactional session scope.

        Yields a SQLAlchemy Session.  Commits on clean exit,
        rolls back on exception.

        Raises:
            SessionCommitError: If the commit fails.
            SessionRollbackError: If the rollback also fails.
        """
        session = self._factory()
        try:
            yield session
            session.commit()
        except Exception:
            try:
                session.rollback()
            except Exception as rollback_exc:
                raise SessionRollbackError(str(rollback_exc)) from rollback_exc
            raise
        finally:
            session.close()

    def create_session(self) -> Session:
        """Create a bare session (caller manages transactions).

        Prefer ``session_scope()`` for most use cases.
        """
        return self._factory()

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return "SessionManager()"
