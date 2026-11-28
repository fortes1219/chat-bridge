"""The embedded PostgreSQL server and the async engine for the app database."""

import platform
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from pgvector.asyncpg import register_vector
from pixeltable_pgserver.postgres_server import PostgresServer, get_server
from sqlalchemy import Column, Connection, Table, event, inspect, text
from sqlalchemy.engine.interfaces import ReflectedColumn
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
    """The local database has tables from another version of the app."""

    def __init__(self, differences: list[str]) -> None:
        super().__init__(
            "the local database was made by another version of chat-bridge "
            f"({'; '.join(differences)}); start the service with `chat-bridge` or run "
            "`chat-bridge ingest <folder>`: either clears the old knowledge base and makes it "
            "again"
        )
        self.differences = differences


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


def stop_server() -> None:
    """Stop the embedded server now if this process is the last one using it.

    The server package stops it at exit. A long-running process calls this as it shuts down,
    because a process that ends by raising its stop signal again never runs its exit hooks.
    A server this process never started is left alone.
    """
    pgdata = pgdata_dir()
    if not (pgdata / "PG_VERSION").exists():
        return
    get_server(pgdata, start=False).cleanup()


def _column_difference(
    name: str, stored: ReflectedColumn | None, expected: Column[Any]
) -> str | None:
    if stored is None:
        return f"{name} is missing"
    if stored["nullable"] != expected.nullable:
        rule = "allows" if stored["nullable"] else "does not allow"
        return f"{name} {rule} NULL"
    return None


def table_differences(connection: Connection, tables: Sequence[Table]) -> list[str]:
    """Columns the given tables lack, and columns whose NULL rule differs from the models. A
    table that does not exist yet is left out: it is made as the model says."""
    inspector = inspect(connection)
    differences: list[str] = []
    for table in tables:
        if not inspector.has_table(table.name):
            continue
        stored = {
            column["name"]: column for column in inspector.get_columns(table.name)
        }
        for column in table.columns:
            name = f"{table.name}.{column.name}"
            difference = _column_difference(name, stored.get(column.name), column)
            if difference:
                differences.append(difference)
    return differences


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

    create_all does not change a table that already exists, so a table from another version
    is reported with SchemaMismatchError instead of failing later in a query.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        differences = await connection.run_sync(
            table_differences, Base.metadata.sorted_tables
        )
    if differences:
        raise SchemaMismatchError(differences)
