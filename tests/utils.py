"""Helpers shared by the tests."""

import asyncio
import shutil
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text

from chat_bridge.config import LOCAL_DATA_ENV, PROJECT_ROOT
from chat_bridge.database import open_engine
from chat_bridge.ingest.service import IngestReport, ingest_folder

TRUTH_DIR = PROJECT_ROOT / "data" / "truth"
PROJECT_LOCAL_DATA = PROJECT_ROOT / "local_data"
DICTIONARY_FILE = Path("jieba") / "dict.txt.big"


def prepare_local_data(folder: Path) -> Path:
    """Make a data folder for a test, with the Traditional Chinese dictionary copied in.

    The dictionary comes from the project's own data folder when it is there, so the tests
    do not download it again; the app still checks its size and hash before using it.
    """
    target = folder / DICTIONARY_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    source = PROJECT_LOCAL_DATA / DICTIONARY_FILE
    if source.is_file():
        shutil.copyfile(source, target)
    return folder


@contextmanager
def using_local_data(folder: Path) -> Iterator[None]:
    """Point the app at another data folder, and so at another embedded database."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv(LOCAL_DATA_ENV, str(folder))
        yield


def copy_sample_files(folder: Path, names: Iterable[str]) -> Path:
    """Copy some of the sample event files into a new folder to ingest."""
    folder.mkdir()
    for name in names:
        shutil.copyfile(TRUTH_DIR / name, folder / name)
    return folder


def ingest(folder: Path) -> IngestReport:
    return asyncio.run(ingest_folder(folder))


def run_sql(statement: str) -> list[Any]:
    """Run one statement in the current data folder's database and return its rows."""

    async def run() -> list[Any]:
        async with open_engine() as engine, engine.begin() as connection:
            result = await connection.execute(text(statement))
            return list(result.all()) if result.returns_rows else []

    return asyncio.run(run())
