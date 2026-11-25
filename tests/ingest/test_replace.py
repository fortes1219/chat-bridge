"""Replacing the stored documents with a folder of one's own.

Each test starts from its own knowledge base of three sample files, with the real embedding
model and the embedded database, so the tests are marked slow.
"""

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest

from chat_bridge.cli import EXIT_ERROR, main
from chat_bridge.search.service import search
from tests.utils import (
    copy_sample_files,
    ingest,
    prepare_local_data,
    run_sql,
    using_local_data,
)

pytestmark = pytest.mark.slow

SAMPLE_FILES = (
    "2026-06-15-nvidia-25-billion-bond.md",
    "2026-11-09-china-extends-tariff-truce.md",
    "2026-11-12-goldman-sees-sp500-8700.md",
)
OWN_FILES = {
    "leave.md": "# 請假規定\n\n員工每年有十四天特休，請假要在三天前提出。\n",
    "faq.txt": "Expense claims are filed within 30 days of the purchase.\n",
}
# A question about one of the sample files, which its own words answer.
SAMPLE_QUESTION = "輝達發行 250 億美元公司債"


@pytest.fixture
def folders(tmp_path: Path) -> Iterator[tuple[Path, Path]]:
    """The sample files, ingested into a database of their own, and a folder of other files."""
    sample = copy_sample_files(tmp_path / "truth", SAMPLE_FILES)
    own = tmp_path / "own"
    own.mkdir()
    for name, content in OWN_FILES.items():
        (own / name).write_text(content, encoding="utf-8", newline="\n")
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        ingest(sample)
        yield sample, own


def _stored_paths() -> list[str]:
    return sorted(row[0] for row in run_sql("SELECT source_path FROM documents"))


def _replace(folder: Path) -> int:
    return main(["ingest", str(folder), "--replace"])


def test_replace_keeps_only_the_folder_and_its_search_entries(
    folders: tuple[Path, Path],
) -> None:
    _, own = folders

    assert _replace(own) == 0

    assert _stored_paths() == sorted(OWN_FILES)
    orphans = run_sql(
        "SELECT count(*) FROM search_entries e LEFT JOIN sections s ON s.id = e.section_id "
        "WHERE s.id IS NULL"
    )
    assert orphans == [(0,)]
    hits = asyncio.run(search(SAMPLE_QUESTION, limit=10)).hits
    assert all(hit.source_path in OWN_FILES for hit in hits)


def test_the_command_lists_what_it_removed(
    folders: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, own = folders

    _replace(own)

    out = capsys.readouterr().out
    assert f"Removed {len(SAMPLE_FILES)} documents that are not in" in out
    assert all(name in out for name in SAMPLE_FILES)


def test_a_file_deleted_from_the_folder_is_removed_on_the_next_replace(
    folders: tuple[Path, Path],
) -> None:
    sample, _ = folders
    (sample / SAMPLE_FILES[0]).unlink()

    assert _replace(sample) == 0

    assert _stored_paths() == sorted(SAMPLE_FILES[1:])


def test_without_replace_the_others_stay_and_the_command_says_so(
    folders: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, own = folders

    assert main(["ingest", str(own)]) == 0

    assert _stored_paths() == sorted([*SAMPLE_FILES, *OWN_FILES])
    out = capsys.readouterr().out
    assert f"also holds {len(SAMPLE_FILES)} documents that are not in" in out
    assert "--replace" in out


def test_a_folder_with_nothing_readable_replaces_nothing(
    folders: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unreadable = tmp_path / "unreadable"
    unreadable.mkdir()
    (unreadable / "notes.odt").write_bytes(b"not read")

    assert _replace(unreadable) == EXIT_ERROR

    assert _stored_paths() == sorted(SAMPLE_FILES)
    assert "nothing was replaced" in capsys.readouterr().err
