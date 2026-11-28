"""The closes a question's lookups need: each market read whole with its listed series, from the
day's store when it serves."""

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from chat_bridge.price_history import day_store
from chat_bridge.price_history.closes import ClosesError
from chat_bridge.price_history.lookups import Lookup, place
from chat_bridge.price_history.markets import Series, market_series
from chat_bridge.price_history.reading import SPAN_DAYS, Reads, read_for

LISTED = market_series()
TAIPEI = ZoneInfo("Asia/Taipei")
NOW = datetime(2026, 11, 28, 10, 0, tzinfo=TAIPEI)
TW_SYMBOLS = ["^TWII", "2330.TW", "2308.TW", "0050.TW", "006208.TW"]
US_SYMBOLS = ["^GSPC", "^IXIC", "^DJI", "^SOX"]


def _frame(days: list[int], close: float = 100.0) -> pd.DataFrame:
    index = pd.DatetimeIndex([pd.Timestamp(2026, 11, day, tz=TAIPEI) for day in days])
    return pd.DataFrame(
        [
            {
                "Open": close,
                "High": close + 1,
                "Low": close - 1,
                "Close": close + n,
                "Volume": 1000.0,
                "Dividends": 0.0,
            }
            for n, _ in enumerate(days)
        ],
        index=index,
    )


class Sources:
    """Stand-in sources that count what is read; each symbol has the sessions given."""

    def __init__(self, days: dict[str, list[int]] | None = None) -> None:
        self.days = days or {}
        self.yahoo: list[tuple[str, date]] = []
        self.backup: list[str] = []
        self.failing: set[str] = set()

    def read_yahoo(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        self.yahoo.append((symbol, start))
        if symbol in self.failing:
            raise ClosesError(f"Yahoo {symbol}: timed out")
        return _frame(self.days.get(symbol, [24, 25, 26, 27]))

    def read_backup(self, series: Series, start: date, end: date) -> dict[date, float]:
        self.backup.append(series.symbol)
        return {date(2026, 11, 24): 90.0}


def _lookup(symbol: str, start: date = date(2026, 11, 2)) -> Lookup:
    series = place(symbol, LISTED, {})
    assert series is not None
    return Lookup(series, start, date(2026, 11, 27))


def _read(
    sources: Sources, lookups: list[Lookup], tmp_path: Path, now: datetime = NOW
) -> Reads:
    return read_for(
        lookups,
        LISTED,
        now,
        read_yahoo=sources.read_yahoo,
        read_backup=sources.read_backup,
        under=tmp_path,
    )


def test_a_symbol_is_read_with_its_markets_listed_series_and_only_that_market(
    tmp_path: Path,
) -> None:
    sources = Sources()

    reads = _read(sources, [_lookup("2454.TW")], tmp_path)

    assert sorted(symbol for symbol, _ in sources.yahoo) == sorted(
        [*TW_SYMBOLS, "2454.TW"]
    )
    assert {start for _, start in sources.yahoo} == {
        date(2026, 11, 2) - timedelta(days=SPAN_DAYS)
    }
    assert set(reads.sessions) == {"TW"}
    assert reads.sessions["TW"] == [date(2026, 11, day) for day in (24, 25, 26, 27)]
    assert not reads.by_symbol["2454.TW"].stored


def test_a_series_that_lacks_a_session_takes_it_from_finmind(tmp_path: Path) -> None:
    sources = Sources({"0050.TW": [25, 26, 27]})

    reads = _read(sources, [_lookup("0050.TW")], tmp_path)

    assert sources.backup == ["0050.TW"]
    found = reads.by_symbol["0050.TW"].closes
    assert found is not None and found.filled == {date(2026, 11, 24)}


def test_a_second_question_within_the_day_reads_nothing(tmp_path: Path) -> None:
    _read(Sources(), [_lookup("2454.TW"), _lookup("NVDA")], tmp_path)
    again = Sources()

    reads = _read(again, [_lookup("2454.TW")], tmp_path, NOW + timedelta(hours=5))

    assert again.yahoo == []
    assert reads.by_symbol["2454.TW"].stored
    assert reads.by_symbol["2454.TW"].read_at == NOW


@pytest.mark.parametrize(
    ("later", "start"),
    [
        pytest.param(timedelta(days=1), date(2026, 11, 2), id="a day later"),
        pytest.param(timedelta(hours=1), date(2026, 9, 1), id="an earlier start"),
    ],
)
def test_a_store_that_does_not_serve_is_read_again_for_the_whole_market(
    tmp_path: Path, later: timedelta, start: date
) -> None:
    _read(Sources(), [_lookup("2454.TW")], tmp_path)
    again = Sources()

    _read(again, [_lookup("2454.TW", start)], tmp_path, NOW + later)

    assert sorted(symbol for symbol, _ in again.yahoo) == sorted(
        [*TW_SYMBOLS, "2454.TW"]
    )


def test_a_market_whose_stored_reads_come_from_two_reads_is_read_again(
    tmp_path: Path,
) -> None:
    _read(Sources(), [_lookup("2454.TW")], tmp_path)
    _read(Sources(), [_lookup("2317.TW")], tmp_path, NOW + timedelta(hours=1))
    again = Sources()

    _read(again, [_lookup("2454.TW")], tmp_path, NOW + timedelta(hours=2))

    assert ("2454.TW", date(2026, 11, 2) - timedelta(days=SPAN_DAYS)) in again.yahoo


def test_a_read_that_cannot_be_kept_is_still_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def full(*args: object, **kwargs: object) -> None:
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(day_store, "save", full)

    reads = _read(Sources(), [_lookup("2454.TW")], tmp_path)

    assert reads.by_symbol["2454.TW"].closes is not None
    assert reads.by_symbol["2454.TW"].error is None
    assert reads.sessions["TW"]


def test_a_store_file_held_open_does_not_stop_the_read(tmp_path: Path) -> None:
    _read(Sources(), [_lookup("2454.TW")], tmp_path)
    # Another question reading the store while this one saves: on Windows the file cannot be
    # replaced while it is open.
    with (tmp_path / "2454.TW.json").open("rb"):
        reads = _read(
            Sources(), [_lookup("2454.TW")], tmp_path, NOW + timedelta(days=2)
        )

    assert reads.by_symbol["2454.TW"].closes is not None
    assert not list(tmp_path.glob("*.part"))


def test_a_symbol_that_cannot_be_read_says_why_and_is_not_kept(tmp_path: Path) -> None:
    sources = Sources()
    sources.failing = {"NVDA"}

    reads = _read(sources, [_lookup("NVDA"), _lookup("2330.TW")], tmp_path)

    assert reads.by_symbol["NVDA"].closes is None
    failure = reads.by_symbol["NVDA"].error
    assert failure is not None and str(failure) == "Yahoo NVDA: timed out"
    assert reads.by_symbol["2330.TW"].closes is not None
    assert day_store.load("NVDA", tmp_path) is None
    assert sorted(path.stem for path in tmp_path.iterdir()) == sorted(
        symbol.replace("^", "_") for symbol in [*TW_SYMBOLS, *US_SYMBOLS]
    )
