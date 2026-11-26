"""The daily closes read once a run: placeholder bars, sessions not ended, and the backup."""

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from chat_bridge.collect import closes as closes_module
from chat_bridge.collect.closes import ClosesError, read_closes, series_from_frame
from chat_bridge.collect.markets import Backup, Market, Series

TAIPEI = ZoneInfo("Asia/Taipei")
TW = Market("TW", "台股", TAIPEI, time(9), time(13, 30))
TAIEX = Series("^TWII", "加權指數", TW, Backup("finmind", "TAIEX"))
TSMC = Series("2330.TW", "台積電 2330", TW, Backup("finmind", "2330"))
AFTER_CLOSE = datetime(2026, 11, 25, 14, 0, tzinfo=TAIPEI)


def _frame(rows: dict[int, dict[str, float]]) -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [pd.Timestamp(2026, 11, day, tz=TAIPEI) for day in rows], name="Date"
    )
    columns = ("Open", "High", "Low", "Close", "Volume", "Dividends")
    return pd.DataFrame(
        [{name: values.get(name, 0.0) for name in columns} for values in rows.values()],
        index=index,
    )


def _bar(close: float, volume: float = 1000.0, **other: float) -> dict[str, float]:
    return {
        "Open": close - 1,
        "High": close + 1,
        "Low": close - 2,
        "Close": close,
        "Volume": volume,
        **other,
    }


def test_a_placeholder_bar_is_not_a_session() -> None:
    frame = _frame(
        {
            21: {"Open": 10.0, "High": 10.0, "Low": 10.0, "Close": 10.0, "Volume": 0.0},
            24: _bar(11.0),
        }
    )

    found = series_from_frame(TW, frame, AFTER_CLOSE)

    assert list(found.closes) == [date(2026, 11, 24)]


def test_the_bar_of_a_session_not_ended_is_not_a_close() -> None:
    during = datetime(2026, 11, 25, 11, 0, tzinfo=TAIPEI)

    found = series_from_frame(TW, _frame({24: _bar(11.0), 25: _bar(12.0)}), during)

    assert list(found.closes) == [date(2026, 11, 24)]


def test_a_day_without_a_close_is_left_out_and_a_dividend_day_kept() -> None:
    frame = _frame(
        {24: _bar(11.0), 25: {**_bar(12.0), "Close": float("nan"), "Dividends": 1.0}}
    )

    found = series_from_frame(TW, frame, AFTER_CLOSE)

    assert list(found.closes) == [date(2026, 11, 24)]
    assert found.dividends == {date(2026, 11, 25)}


def test_the_backup_fills_only_a_series_that_lacks_a_session_day() -> None:
    frames = {
        "^TWII": _frame({24: _bar(40122.35), 25: _bar(38195.43)}),
        "2330.TW": _frame({24: _bar(2230.0)}),
    }
    asked: list[str] = []

    def backup(series: Series, start: date, end: date) -> dict[date, float]:
        asked.append(series.symbol)
        return {date(2026, 11, 24): 2230.0, date(2026, 11, 25): 2150.0}

    found = read_closes(
        [TAIEX, TSMC],
        date(2026, 11, 20),
        date(2026, 11, 25),
        AFTER_CLOSE,
        read_yahoo=lambda symbol, start, end: frames[symbol],
        read_backup=backup,
    )

    assert asked == ["2330.TW"]
    assert found["2330.TW"].closes[date(2026, 11, 25)] == 2150.0
    assert found["2330.TW"].filled == {date(2026, 11, 25)}
    assert found["^TWII"].filled == set()


def test_a_source_that_cannot_be_read_stops_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Empty:
        def __init__(self, symbol: str) -> None:
            pass

        def history(self, **kwargs: Any) -> pd.DataFrame:
            return pd.DataFrame()

    monkeypatch.setattr(closes_module.yf, "Ticker", Empty)

    with pytest.raises(ClosesError, match=r"Yahoo \^TWII: no daily data"):
        read_closes([TAIEX], date(2026, 11, 20), date(2026, 11, 25), AFTER_CLOSE)
