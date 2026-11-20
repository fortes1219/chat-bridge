"""Helpers shared by the tests."""

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from chat_bridge.config import LOCAL_DATA_ENV, PROJECT_ROOT

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
