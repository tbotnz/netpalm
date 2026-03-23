"""
Alembic environment configuration for netpalm.

Uses async SQLAlchemy engine (asyncpg) with the run_async_migrations() pattern.
The database URL is read from NetpalmSettings (NETPALM_DATABASE_URL env var takes
precedence over config files, which takes precedence over alembic.ini).
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import ORM metadata so autogenerate can detect schema changes.
# netpalm.backend.core.db is created in task 3.1; import is guarded so that
# alembic CLI commands still work before that module exists.
# ---------------------------------------------------------------------------
try:
    from netpalm.backend.core.models.db_models import Base  # noqa: F401

    target_metadata = Base.metadata
except ImportError:
    # Task 3.1 not yet implemented — autogenerate will produce an empty migration.
    target_metadata = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from environment / NetpalmSettings if available.
# ---------------------------------------------------------------------------
_db_url = os.environ.get("NETPALM_DATABASE_URL")
if _db_url:
    config.set_main_option("sqlalchemy.url", _db_url)
else:
    # Try to load from NetpalmSettings (may not be available yet in early tasks)
    try:
        from netpalm.backend.core.confload.confload import get_settings  # type: ignore[import]

        config.set_main_option("sqlalchemy.url", get_settings().database_url)
    except Exception:
        pass  # Fall back to alembic.ini value


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
