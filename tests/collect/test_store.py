"""The events `collect` stores for `truth`: written whole, read back, removed only when they are
stored events of the collected folder."""

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from chat_bridge.collect import store
from chat_bridge.collect.store import StoredEvent, StoreError
from tests.truth.stand_ins import CNA, FED, FOUND_DATE, PAGES

SINCE = date(2026, 11, 18)


def test_an_event_is_stored_with_its_pages_text_and_read_back(tmp_path: Path) -> None:
    folder = store.store(tmp_path, FOUND_DATE, "The Fed holds", SINCE, None, PAGES)

    assert folder is not None
    assert sorted(path.name for path in folder.iterdir()) == [
        "event.json",
        "s1.txt",
        "s2.txt",
    ]
    assert folder.name.startswith("2026-11-24-") and len(folder.name) == 23
    (event,) = store.stored_events(tmp_path)
    assert (event.event_date, event.about, event.since, event.until) == (
        FOUND_DATE,
        "The Fed holds",
        SINCE,
        None,
    )
    assert event.read_pages() == PAGES
    # Nothing is left beside it.
    assert [path.name for path in tmp_path.iterdir()] == [folder.name]


def test_the_same_pages_are_not_stored_twice(tmp_path: Path) -> None:
    store.store(tmp_path, FOUND_DATE, "first", SINCE, None, PAGES)

    assert store.store(tmp_path, FOUND_DATE, "again", SINCE, None, (CNA, FED)) is None
    assert len(store.stored_events(tmp_path)) == 1


def test_stored_events_can_start_from_a_date(tmp_path: Path) -> None:
    store.store(tmp_path, date(2026, 11, 17), "earlier", None, None, (FED,))
    store.store(tmp_path, FOUND_DATE, "later", None, None, (CNA,))

    assert [one.about for one in store.stored_events(tmp_path, SINCE)] == ["later"]
    assert [one.about for one in store.stored_events(tmp_path)] == ["earlier", "later"]


def test_removing_the_last_event_leaves_no_collected_folder(tmp_path: Path) -> None:
    root = tmp_path / "collected"
    store.store(root, FOUND_DATE, "only", SINCE, None, PAGES)
    (event,) = store.stored_events(root)

    store.remove(root, event)

    assert not root.exists()


@pytest.mark.parametrize(
    "name",
    ["notes", "2026-11-24-0123456789ab"],
    ids=["not an event name", "no event.json"],
)
def test_only_a_stored_event_of_the_folder_is_removed(
    tmp_path: Path, name: str
) -> None:
    root = tmp_path / "collected"
    other = root / name
    other.mkdir(parents=True)
    (other / "keep.txt").write_text("x", encoding="utf-8")
    event = StoredEvent(other, FOUND_DATE, "x", None, None)

    with pytest.raises(StoreError, match="not an event stored"):
        store.remove(root, event)
    assert (other / "keep.txt").is_file()


def test_a_folder_outside_the_collected_folder_is_not_removed(tmp_path: Path) -> None:
    root = tmp_path / "collected"
    store.store(root, FOUND_DATE, "x", SINCE, None, PAGES)
    (event,) = store.stored_events(root)
    elsewhere = replace(event, folder=tmp_path / event.folder.name)
    elsewhere.folder.mkdir()
    (elsewhere.folder / "event.json").write_text("{}", encoding="utf-8")

    with pytest.raises(StoreError):
        store.remove(root, elsewhere)
    assert elsewhere.folder.is_dir()


def test_an_event_folder_that_cannot_be_read_is_named(tmp_path: Path) -> None:
    broken = tmp_path / "2026-11-24-0123456789ab"
    broken.mkdir()
    (broken / "event.json").write_text("{", encoding="utf-8")

    with pytest.raises(StoreError, match="2026-11-24-0123456789ab"):
        store.stored_events(tmp_path)
