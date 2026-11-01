"""Alembic environment configuration for ACIS.

Reads the database URL from the application settings (environment / .env),
so migrations never embed credentials. Supports offline mode (no live
PostgreSQL required) for `alembic revision --autogenerate --sql` and online
migrations once PostgreSQL + pgvector are available.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Import the ACIS app so we can reuse its declarative Base and settings.
# ``prepend_sys_path = .`` in alembic.ini places the backend directory on sys.path.
from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# Import ORM models so they register on Base.metadata for autogenerate support.
from app.models.research import Research  # noqa: E402,F401
from app.models.company import CompanyProfile, EvidenceClaim  # noqa: E402,F401
from app.models.competitor import Competitor, CompetitorEvidence  # noqa: E402,F401

# pgvector types are imported for metadata completeness; the migration itself
# uses SQLAlchemy core types so it remains runnable even before pgvector is
# installed (pgvector column support is added when PostgreSQL is provisioned).
try:
    from pgvector.sqlalchemy import Vector  # noqa: F401
except Exception:  # pragma: no cover - optional until PG is provisioned
    Vector = None

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Resolve the database URL from settings, never hardcoded."""
    settings = get_settings()
    url = settings.database_url or ""
    if not url:
        return ""
    # Ensure an async dialect for the async engine used in online migrations.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations without a live database (generates SQL only)."""
    url = get_url()
    if not url:
        # No DATABASE_URL configured: emit a notice and run offline against a
        # placeholder so `alembic revision --sql` still works in dev/CI.
        url = "postgresql+asyncpg://localhost/dbname"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database (requires PostgreSQL)."""
    url = get_url()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL to run online migrations."
        )
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async def run_async() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda sync_conn: context.configure(
                    connection=sync_conn,
                    target_metadata=target_metadata,
                    compare_type=True,
                    render_as_batch=True,
                )
            )
            async with connection.begin():
                await connection.run_sync(lambda _: context.run_migrations())

    import asyncio

    asyncio.run(run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
