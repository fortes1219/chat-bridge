"""Searching as of a date: only files whose event happened on or before that day.

The filter works on whole files by their event date. These tests check that, not that the
hits hold nothing learned later: a file's own later sections, such as the market moves in
the days after its event, stay in.
"""

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest

from chat_bridge.cli import main
from chat_bridge.database import DATABASE_NAME
from chat_bridge.search.service import SearchHit, SearchResult, search
from tests.utils import (
    copy_sample_files,
    ingest,
    prepare_local_data,
    run_sql,
    using_local_data,
)

pytestmark = pytest.mark.slow

QUESTION = "台股重挫"
EARLY_DAY = date(2026, 6, 8)
# Many later files talk about the Fed raising rates; this early one mentions both too.
CROWDED_QUESTION = "聯準會升息"
CROWDED_OUT_FILE = "2026-06-05-us-tech-selloff-broadcom-jobs.md"

DATED_FILES = (
    "2026-06-15-nvidia-25-billion-bond.md",
    "2026-11-12-goldman-sees-sp500-8700.md",
)
UNDATED_FILE = "undated-note.md"
UNDATED_WORDS = "無日期筆記"


def search_as_of(question: str, limit: int, as_of: date | None = None) -> SearchResult:
    return asyncio.run(search(question, limit, as_of))


def paths(hits: list[SearchHit]) -> list[str]:
    return [hit.source_path for hit in hits]


@contextmanager
def database_setting(name: str, value: str) -> Iterator[None]:
    """Set a planner setting for every new connection to the database, then reset it."""
    run_sql(f"ALTER DATABASE {DATABASE_NAME} SET {name} = {value}")
    try:
        yield
    finally:
        run_sql(f"ALTER DATABASE {DATABASE_NAME} RESET {name}")


# ------------------------------------------------------------- All 71 sample files


def test_every_hit_comes_from_a_file_dated_on_or_before_the_day(
    sample_knowledge_base: None,
) -> None:
    day = date(2026, 7, 31)

    hits = search_as_of(QUESTION, 10, day).hits

    assert hits
    assert all(hit.event_date is not None and hit.event_date <= day for hit in hits)


def test_the_date_filter_applies_before_the_candidates_are_taken(
    sample_knowledge_base: None,
) -> None:
    # Without a date, so many later files match that the early one is not among either
    # method's candidates: 40 hits cover both lists of 20. Filtering after the candidates
    # were taken would leave it out of the dated search too.
    assert CROWDED_OUT_FILE not in paths(search_as_of(CROWDED_QUESTION, 40).hits)

    assert CROWDED_OUT_FILE in paths(search_as_of(CROWDED_QUESTION, 5, EARLY_DAY).hits)


def test_a_day_before_every_event_finds_nothing(sample_knowledge_base: None) -> None:
    assert search_as_of(QUESTION, 5, date(2026, 1, 1)).hits == []


def test_the_vector_index_finds_what_an_exact_scan_finds(
    sample_knowledge_base: None,
) -> None:
    # With a filter, an HNSW scan only sees its first candidates unless iterative scans
    # go on looking; an early date leaves few rows, so a missing iterative scan shows here.
    with database_setting("enable_indexscan", "off"):
        exact = search_as_of(QUESTION, 10, EARLY_DAY).hits
    with database_setting("enable_seqscan", "off"):
        indexed = search_as_of(QUESTION, 10, EARLY_DAY).hits

    assert exact
    assert indexed == exact


# ------------------------------------------------------- A file without a date


@pytest.fixture
def knowledge_base_with_an_undated_file(tmp_path: Path) -> Iterator[Path]:
    folder = copy_sample_files(tmp_path / "files", DATED_FILES)
    (folder / UNDATED_FILE).write_text(
        f"# 筆記\n\n{UNDATED_WORDS}：這一份沒有事件日期。\n",
        encoding="utf-8",
        newline="\n",
    )
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        ingest(folder)
        yield folder


def test_a_file_without_an_event_date_is_found_without_a_date(
    knowledge_base_with_an_undated_file: Path,
) -> None:
    result = search_as_of(UNDATED_WORDS, 5)

    assert paths(result.hits)[:1] == [UNDATED_FILE]
    assert result.undated_left_out == 0


def test_a_file_without_an_event_date_is_left_out_and_counted(
    knowledge_base_with_an_undated_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = search_as_of(UNDATED_WORDS, 5, date(2026, 12, 31))

    assert UNDATED_FILE not in paths(result.hits)
    assert result.undated_left_out == 1

    main(["search", UNDATED_WORDS, "--as-of", "2026-12-31"])
    assert "Files left out for having no event date: 1." in capsys.readouterr().out
