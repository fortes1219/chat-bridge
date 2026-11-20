"""What a second ingest does to a stored knowledge base, and when search refuses it.

Each test starts from its own knowledge base of three sample files, with the real embedding
model and the embedded database, so the tests are marked slow.
"""

import asyncio
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select, text

from chat_bridge.database import open_engine
from chat_bridge.ingest.models import Document, SearchEntry, Section
from chat_bridge.ingest.service import IndexUpdate, IngestReport, ingest_folder
from chat_bridge.search.service import IndexMismatchError, search
from tests.utils import TRUTH_DIR, prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

SAMPLE_FILES = (
    "2026-06-15-nvidia-25-billion-bond.md",
    "2026-11-09-china-extends-tariff-truce.md",
    "2026-11-12-goldman-sees-sp500-8700.md",
)
EDITED_FILE = "2026-11-12-goldman-sees-sp500-8700.md"
NEW_KEYWORD = "測試專用詞"


def ingest(folder: Path) -> IngestReport:
    return asyncio.run(ingest_folder(folder))


@pytest.fixture
def knowledge_base(tmp_path: Path) -> Iterator[Path]:
    """A folder of three sample files, already ingested into a database of its own."""
    folder = tmp_path / "truth"
    folder.mkdir()
    for name in SAMPLE_FILES:
        shutil.copyfile(TRUTH_DIR / name, folder / name)
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        report = ingest(folder)
        assert report.index_update == IndexUpdate.ALL
        assert sorted(report.written) == sorted(SAMPLE_FILES)
        yield folder


async def _stored_embeddings() -> dict[str, dict[int, list[float] | None]]:
    query = (
        select(Document.source_path, SearchEntry.id, SearchEntry.embedding_bge_m3)
        .join(Section, SearchEntry.section_id == Section.id)
        .join(Document, Section.document_id == Document.id)
    )
    stored: dict[str, dict[int, list[float] | None]] = {}
    async with open_engine() as engine, engine.connect() as connection:
        for row in await connection.execute(query):
            vector: Any = row.embedding_bge_m3
            stored.setdefault(row.source_path, {})[row.id] = (
                None if vector is None else [float(value) for value in vector]
            )
    return stored


def stored_embeddings_except(edited: str) -> dict[str, dict[int, list[float] | None]]:
    """Every stored entry's embedding, by file and entry id, for the files not edited."""
    stored = asyncio.run(_stored_embeddings())
    return {path: entries for path, entries in stored.items() if path != edited}


def run_sql(statement: str) -> list[Any]:
    async def run() -> list[Any]:
        async with open_engine() as engine, engine.begin() as connection:
            result = await connection.execute(text(statement))
            return list(result.all()) if result.returns_rows else []

    return asyncio.run(run())


def edit(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content
    path.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")


def test_unchanged_files_are_skipped(knowledge_base: Path) -> None:
    report = ingest(knowledge_base)

    assert report.written == []
    assert sorted(report.unchanged) == sorted(SAMPLE_FILES)
    assert report.index_update == IndexUpdate.NONE


def test_a_changed_body_rewrites_only_that_file(knowledge_base: Path) -> None:
    others_before = stored_embeddings_except(EDITED_FILE)
    edit(
        knowledge_base / EDITED_FILE,
        "## 影響股市證據",
        "A new line.\n\n## 影響股市證據",
    )

    report = ingest(knowledge_base)

    assert report.written == [EDITED_FILE]
    assert report.index_update == IndexUpdate.WRITTEN_FILES
    assert stored_embeddings_except(EDITED_FILE) == others_before


def test_a_new_keyword_rebuilds_only_the_words(knowledge_base: Path) -> None:
    others_before = stored_embeddings_except(EDITED_FILE)
    edit(
        knowledge_base / EDITED_FILE,
        "keyword_groups:\n",
        f"keyword_groups:\n  - [{NEW_KEYWORD}]\n",
    )

    report = ingest(knowledge_base)

    assert report.written == [EDITED_FILE]
    assert report.index_update == IndexUpdate.KEYWORDS
    assert stored_embeddings_except(EDITED_FILE) == others_before
    hits = asyncio.run(search(NEW_KEYWORD, 3)).hits
    assert hits and hits[0].source_path == EDITED_FILE


def test_a_write_leaves_no_dead_rows(knowledge_base: Path) -> None:
    # Rebuilding the words updates every row, which leaves one dead row behind for each.
    edit(
        knowledge_base / EDITED_FILE,
        "keyword_groups:\n",
        f"keyword_groups:\n  - [{NEW_KEYWORD}]\n",
    )
    ingest(knowledge_base)

    [(dead_rows, last_vacuum)] = run_sql(
        "SELECT n_dead_tup, last_vacuum FROM pg_stat_user_tables "
        "WHERE relname = 'search_entries'"
    )
    assert dead_rows == 0
    assert last_vacuum is not None


@pytest.mark.parametrize(
    "statement",
    [
        pytest.param(
            "UPDATE embedding_state SET model_revision = 'other'", id="another model"
        ),
        pytest.param(
            "UPDATE entry_layout_state SET layout = 'other'", id="another layout"
        ),
    ],
)
def test_search_refuses_an_index_built_another_way(
    knowledge_base: Path, statement: str
) -> None:
    run_sql(statement)

    with pytest.raises(IndexMismatchError):
        asyncio.run(search("高盛", 3))
