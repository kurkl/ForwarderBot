import asyncio
from logging.config import fileConfig

from alembic import context
from environs import Env
from sqlalchemy import pool, engine_from_config
from sqlalchemy.ext.asyncio import AsyncEngine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# TODO: import db url from app config
env = Env()
env.read_env(".env.dev")
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

config = context.config
import sys  # noqa

sys.path.append("")

from src.database import BaseModel  # noqa

target_metadata = BaseModel.metadata


def get_uri():
    db_path = env.str("SQLALCHEMY_DB_URI")
    return db_path


sqlalchemy_db_uri = get_uri()

config.set_main_option("sqlalchemy.url", sqlalchemy_db_uri)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
