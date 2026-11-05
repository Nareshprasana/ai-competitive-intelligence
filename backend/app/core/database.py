"""SQLAlchemy database engine, session management, and pgvector preparation.

Design goals:
- The application must start and run without a running PostgreSQL instance.
- Database-backed functionality degrades gracefully and reports itself as
  unavailable (never falsely reports a successful connection).
- Engine creation is lazy: it does not connect at import time.
- pgvector compatibility is prepared via the ``pgvector`` SQLAlchemy types so
  migrations can use vector columns once PostgreSQL is available.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

from psycopg import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.checkpoint import AsyncPostgresSaver
from app.core.config import get_settings
from app.core.exceptions import DatabaseUnavailableError
from app.core.logging import get_logger
from app.security.crypto import EncryptedCheckpointSerializer

logger = get_logger("app.core.database")


class Base(DeclarativeBase):
    """Declarative base for all ACIS ORM models."""


class DatabaseManager:
    """Manages the SQLAlchemy async engine, session factory, and checkpointer.

    The engine is created lazily on first use. If no DATABASE_URL is configured
    (or the database cannot be reached), operations raise
    ``DatabaseUnavailableError`` with a clear message instead of failing
    silently or reporting a false connection.

    LangGraph checkpoint state is stored in dedicated ``checkpoints`` /
    ``checkpoint_writes`` tables (created by ``AsyncPostgresSaver.setup()``),
    SEPARATE from the business ``researches`` table owned by
    :class:`app.repositories.research.ResearchRepository`.
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._checkpointer: Optional[AsyncPostgresSaver] = None
        self._configured: bool = False
        self._available: bool = False

    def _ensure_configured(self) -> None:
        if self._configured:
            return
        settings = get_settings()
        database_url = settings.database_url
        if not database_url:
            logger.warning(
                "DATABASE_URL not configured; database-backed features will be unavailable."
            )
            self._configured = True
            self._available = False
            return

        # Normalize async driver: ensure an async dialect is used.
        async_url = self._to_async_url(database_url)
        self._engine = create_async_engine(
            async_url,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._configured = True
        self._available = True
        logger.info("Database engine configured (lazy; connection established on first use).")

    @staticmethod
    def _to_async_url(url: str) -> str:
        """Rewrite a database URL to use an async driver where possible."""
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @staticmethod
    def _to_libpq_url(url: str) -> str:
        """Rewrite a SQLAlchemy async URL into a libpq connection string.

        ``AsyncPostgresSaver`` (psycopg-based) needs a ``postgresql://`` URL,
        not SQLAlchemy's ``postgresql+asyncpg://`` form.
        """
        libpq = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        libpq = libpq.replace("postgresql://", "postgresql://", 1)  # idempotent guard
        return libpq

    def checkpointer_url(self) -> Optional[str]:
        """Return a libpq URL for the LangGraph checkpointer, or None."""
        settings = get_settings()
        url = settings.langgraph_checkpoint_database_url or settings.database_url
        if not url:
            return None
        return self._to_libpq_url(url)

    async def get_checkpointer(self) -> AsyncPostgresSaver:
        """Create (and cache) a LangGraph PostgreSQL checkpointer.

        Calls ``setup()`` to create the dedicated checkpoints tables. Returns
        the same instance on subsequent calls.
        """
        if self._checkpointer is not None:
            return self._checkpointer

        self._ensure_configured()
        if not self._available:
            raise DatabaseUnavailableError(
                "Database is not configured; cannot create LangGraph checkpointer.",
                details={"hint": "Set DATABASE_URL in environment or .env"},
            )

        url = self.checkpointer_url()
        if not url:
            raise DatabaseUnavailableError(
                "No checkpoint database URL configured.",
                details={"hint": "Set DATABASE_URL or LANGGRAPH_CHECKPOINT_DATABASE_URL"},
            )

        # Open a dedicated psycopg connection for the checkpointer (separate
        # from the SQLAlchemy async engine used by the research repository).
        conn = await asyncio.to_thread(
            Connection.connect, url, autocommit=True, prepare_threshold=0
        )
        saver = AsyncPostgresSaver(conn, serde=EncryptedCheckpointSerializer())
        try:
            await asyncio.to_thread(saver.setup)
        except Exception:
            await asyncio.to_thread(conn.close)
            raise
        self._checkpointer = saver
        logger.info("LangGraph PostgreSQL checkpointer configured.")
        return self._checkpointer

    async def dispose_checkpointer(self) -> None:
        """Release the checkpointer connection (clean shutdown)."""
        if self._checkpointer is not None:
            try:
                await asyncio.to_thread(self._checkpointer.conn.close)
            except Exception:  # noqa: BLE001 - best-effort cleanup
                logger.debug("Error closing checkpointer connection.", exc_info=True)
            self._checkpointer = None

    @property
    def is_available(self) -> bool:
        """Whether a database engine has been configured."""
        self._ensure_configured()
        return self._available

    @property
    def engine(self) -> AsyncEngine:
        """Return the configured engine, raising if unavailable."""
        self._ensure_configured()
        if self._engine is None:
            raise DatabaseUnavailableError(
                "Database is not configured. Set DATABASE_URL to enable database-backed features.",
                details={"hint": "Provide DATABASE_URL in environment or .env"},
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Return the session factory, raising if unavailable."""
        self._ensure_configured()
        if self._session_factory is None:
            raise DatabaseUnavailableError(
                "Database session factory is not configured. Set DATABASE_URL to enable database-backed features.",
                details={"hint": "Provide DATABASE_URL in environment or .env"},
            )
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield an async SQLAlchemy session. Raises if database unavailable."""
        factory = self.session_factory
        async with factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def health_check(self) -> Dict[str, object]:
        """Return database availability status without raising.

        Performs a lightweight ``SELECT 1`` only when a database is configured.
        Never raises; returns a dict describing the status.
        """
        self._ensure_configured()
        if not self._available or self._engine is None:
            return {
                "available": False,
                "configured": False,
                "error": "DATABASE_URL not configured",
            }

        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
            return {
                "available": True,
                "configured": True,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - report any connectivity failure
            logger.warning(
                "Database health check failed error_type=%s", type(exc).__name__
            )
            return {
                "available": False,
                "configured": True,
                "error": "Database connection failed",
            }

    async def dispose(self) -> None:
        """Dispose of the engine (clean shutdown)."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Singleton instance used across the application.
db = DatabaseManager()


# Dependency for FastAPI endpoints.
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session.

    Raises ``DatabaseUnavailableError`` when no database is configured.
    """
    async for session in db.get_session():
        yield session


# For Alembic: expose a synchronous-ish URL helper.
def get_sync_database_url() -> Optional[str]:
    """Return a sync database URL suitable for Alembic offline migrations."""
    settings = get_settings()
    return settings.database_url


try:
    from pgvector.sqlalchemy import Vector  # noqa: F401

    PGVECTOR_AVAILABLE = True
except Exception:  # pragma: no cover - pgvector optional until PG present
    PGVECTOR_AVAILABLE = False
    logger.debug("pgvector SQLAlchemy types not installed; vector columns unavailable.")


__all__ = [
    "Base",
    "DatabaseManager",
    "db",
    "get_db_session",
    "get_sync_database_url",
    "PGVECTOR_AVAILABLE",
    "DatabaseUnavailableError",
]
