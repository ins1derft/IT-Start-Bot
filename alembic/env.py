from __future__ import annotations

import os
from logging.config import fileConfig

import asyncio
import os
from sqlalchemy import pool
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section)
    url = os.getenv("POSTGRES_DSN") or section.get("sqlalchemy.url")
    connectable: AsyncEngine = async_engine_from_config(
        {**section, "sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    def do_migrations(connection: Connection) -> None:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

    async def do_run_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_migrations)

    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
