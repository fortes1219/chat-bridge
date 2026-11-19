"""The embedded PostgreSQL server and the async engine for the app database."""

import platform
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pixeltable_pgserver.postgres_server import PostgresServer, get_server
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from chat_bridge.config import local_data_dir

DATABASE_NAME = "chat_bridge"
DRIVER = "asyncpg"

# Collation C gives the same sort order on every machine. The character type follows
# pixeltable, the main user of the embedded server package, per platform.
LC_CTYPE_BY_PLATFORM = {"Windows": ".UTF-8", "Darwin": "en_US.UTF-8"}
DEFAULT_LC_CTYPE = "C.UTF-8"


class Base(DeclarativeBase):
    pass


def _create_database_statement() -> str:
    lc_ctype = LC_CTYPE_BY_PLATFORM.get(platform.system(), DEFAULT_LC_CTYPE)
    return (
        f"CREATE DATABASE {DATABASE_NAME} TEMPLATE template0 ENCODING 'UTF8' "
        f"LC_COLLATE 'C' LC_CTYPE '{lc_ctype}'"
    )


async def _ensure_database(server: PostgresServer) -> None:
    # CREATE DATABASE cannot run inside a transaction, so this engine autocommits.
    engine = create_async_engine(
        server.get_uri(database="postgres", driver=DRIVER), isolation_level="AUTOCOMMIT"
    )
    try:
        async with engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": DATABASE_NAME},
            )
            if exists is None:
                await connection.execute(text(_create_database_statement()))
    finally:
        await engine.dispose()


@asynccontextmanager
async def open_engine() -> AsyncIterator[AsyncEngine]:
    """Start or join the embedded server, make sure the app database exists, and yield an engine.

    The server stops when the last process that uses it exits, so no server is left behind.
    """
    server = get_server(local_data_dir() / "pgdata")
    await _ensure_database(server)
    engine = create_async_engine(server.get_uri(database=DATABASE_NAME, driver=DRIVER))
    try:
        yield engine
    finally:
        await engine.dispose()


async def create_tables(engine: AsyncEngine) -> None:
    """Create the tables of every model module the caller has imported. Existing tables are kept."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
