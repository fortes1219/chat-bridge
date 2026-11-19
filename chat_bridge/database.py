"""The embedded PostgreSQL server and the async engine for the app database."""

import platform
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from pgvector.asyncpg import register_vector
from pixeltable_pgserver.postgres_server import PostgresServer, get_server
from sqlalchemy import Connection, event, inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from chat_bridge.config import local_data_dir
from chat_bridge.errors import LocalSetupError

DATABASE_NAME = "chat_bridge"
DRIVER = "asyncpg"

# Collation C gives the same sort order on every machine. The character type follows
# pixeltable, the main user of the embedded server package, per platform.
LC_CTYPE_BY_PLATFORM = {"Windows": ".UTF-8", "Darwin": "en_US.UTF-8"}
DEFAULT_LC_CTYPE = "C.UTF-8"


class Base(DeclarativeBase):
    pass


class SchemaMismatchError(LocalSetupError):
    """The local database has tables from an older version of the app, without some columns."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            f"the local database was made by an older version and lacks {', '.join(missing)}; "
            f"delete {pgdata_dir()} and run `chat-bridge ingest <folder>` again"
        )
        self.missing = missing


def pgdata_dir() -> Path:
    return local_data_dir() / "pgdata"


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

    # pgvector is enabled right after the database exists, as pixeltable does, so the
    # engine below can register the vector type on every connection.
    engine = create_async_engine(
        server.get_uri(database=DATABASE_NAME, driver=DRIVER),
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        await engine.dispose()


@asynccontextmanager
async def open_engine() -> AsyncIterator[AsyncEngine]:
    """Start or join the embedded server, make sure the app database exists, and yield an engine.

    The server stops when the last process that uses it exits, so no server is left behind.
    """
    server = get_server(pgdata_dir())
    await _ensure_database(server)
    engine = create_async_engine(server.get_uri(database=DATABASE_NAME, driver=DRIVER))

    # The Azure template registers pgvector's asyncpg codec on each new connection.
    @event.listens_for(engine.sync_engine, "connect")
    def _register_vector(dbapi_connection: Any, _record: Any) -> None:
        dbapi_connection.run_async(register_vector)

    try:
        yield engine
    finally:
        await engine.dispose()


def _missing_columns(connection: Connection) -> list[str]:
    inspector = inspect(connection)
    missing: list[str] = []
    for table in Base.metadata.sorted_tables:
        existing = {column["name"] for column in inspector.get_columns(table.name)}
        missing.extend(
            f"{table.name}.{column.name}"
            for column in table.columns
            if column.name not in existing
        )
    return missing


async def vacuum(engine: AsyncEngine) -> None:
    """Remove dead rows and refresh the planner's statistics, as autovacuum would.

    PostgreSQL's autovacuum looks at a database at most once per autovacuum_naptime, one
    minute by default. The embedded server runs only while a command runs, a few seconds, so
    autovacuum never gets its turn. Dead rows then pile up, and pgvector's README warns that
    dead tuples leave an HNSW scan with fewer results: the index stops finding the nearest
    rows. A command that wrote to the database calls this after its transaction commits.
    """
    # VACUUM cannot run inside a transaction block.
    async with engine.connect() as connection:
        autocommit = await connection.execution_options(isolation_level="AUTOCOMMIT")
        await autocommit.execute(text("VACUUM (ANALYZE)"))


async def create_tables(engine: AsyncEngine) -> None:
    """Create the tables of every model module the caller has imported. Existing tables are kept.

    create_all does not add columns to a table that already exists, so a table from an older
    version is reported with SchemaMismatchError instead of failing later in a query.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        missing = await connection.run_sync(_missing_columns)
    if missing:
        raise SchemaMismatchError(missing)
