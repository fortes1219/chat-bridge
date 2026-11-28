"""What was read is kept for a day, one file a series."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from chat_bridge.price_history import day_store
from chat_bridge.price_history.closes import SeriesCloses

READ_AT = datetime(2026, 11, 28, 2, 0, tzinfo=UTC)
CLOSES = SeriesCloses(
    {date(2026, 11, 24): 95.69999694824219, date(2026, 11, 25): 90.3},
    {date(2026, 11, 24)},
    {date(2026, 10, 20)},
)


def test_a_read_comes_back_exactly_as_it_was_kept(tmp_path: Path) -> None:
    day_store.save("^TWII", date(2026, 9, 1), READ_AT, CLOSES, tmp_path)

    stored = day_store.load("^TWII", tmp_path)

    assert stored is not None
    assert stored.closes == CLOSES
    assert (stored.start, stored.read_at) == (date(2026, 9, 1), READ_AT)
    assert [path.name for path in tmp_path.iterdir()] == ["_TWII.json"]


def test_a_read_serves_for_a_day_from_its_start() -> None:
    stored = day_store.Stored(date(2026, 9, 1), READ_AT, CLOSES)
    later = READ_AT + timedelta(hours=23, minutes=59)

    assert day_store.serves(stored, date(2026, 9, 1), later)
    assert not day_store.serves(stored, date(2026, 9, 1), READ_AT + timedelta(days=1))
    assert not day_store.serves(stored, date(2026, 8, 31), later)
    assert not day_store.serves(None, date(2026, 9, 1), later)


def test_a_file_that_cannot_be_read_is_not_a_read(tmp_path: Path) -> None:
    (tmp_path / "NVDA.json").write_text("{not json", encoding="utf-8")
    day_store.save("AAPL", date(2026, 9, 1), READ_AT, CLOSES, tmp_path)
    (tmp_path / "AAPL.json").rename(tmp_path / "MSFT.json")

    assert day_store.load("NVDA", tmp_path) is None
    assert day_store.load("MSFT", tmp_path) is None
    assert day_store.load("TSLA", tmp_path) is None
