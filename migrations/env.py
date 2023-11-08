from __future__ import with_statement
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.future import Connection
from logging.config import fileConfig

import asyncio
import os
import sys

# prepend the app directory to the system path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

# Alembic Config object
config = context.config

# Set up loggers
fileConfig(config.config_file_name)

# Import your model's MetaData object for 'autogenerate' support
from src import model

target_metadata = model.Base.metadata


# Function to get the database URI
def get_uri():
    return os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


# Async migration runner for 'offline' mode
async def run_migrations_offline():
    url = get_uri()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


# Async migration runner for 'online' mode
async def run_migrations_online():
    connectable: AsyncEngine = create_async_engine(get_uri())

    async with connectable.connect() as connection:
        await connection.run_sync(
            context.configure, connection=connection, target_metadata=target_metadata
        )

        async with connection.begin():
            await context.run_migrations()


# Main entry point
def main():
    if context.is_offline_mode():
        asyncio.run(run_migrations_offline())
    else:
        asyncio.run(run_migrations_online())


if __name__ == "env":
    main()
