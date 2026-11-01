"""FastAPI dependency injection providers."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.core.database import get_db_session, db
from app.core.logging import get_logger

logger = get_logger("app.dependencies")


async def get_session() -> AsyncGenerator:
    """Yield a database session, or raise DatabaseUnavailableError."""
    async for session in get_db_session():
        yield session


async def database_health() -> dict:
    """Return database health status (never raises)."""
    return await db.health_check()


SessionDep = Annotated[object, Depends(get_session)]
