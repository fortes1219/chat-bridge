"""The daily closes of the series over a span, read once a run for every news file.

Yahoo's daily series is the first source; a day it lacks of a series with a backup comes from
that backup (FinMind for the Taiwan series). A market's sessions are the days any of its series
closed on. A bar Yahoo adds with no volume and the same open, high, low and close is its
placeholder for a day without trading, not a session; the bar of a session that has not ended
when the data is read is its latest price, not a close, and is left out.

The closes stay the floats Yahoo gives, unadjusted for dividends, so a change is worked out on the
same numbers as the earlier files' sections and the same data gives the same text.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import pandas as pd
import yfinance as yf

from chat_bridge.collect.markets import Market, Series
from chat_bridge.strategy.taiwan_sources import SourceError, finmind_closes

logger = logging.getLogger(__name__)

# Where each source is named in a news file's `sources` and in the section's notes.
YAHOO = "Yahoo"
BACKUP_NAMES = {"finmind": "FinMind"}


class ClosesError(Exception):
    """A source of daily closes could not be read. The message names it."""


@dataclass
class SeriesCloses:
    closes: dict[date, float] = field(default_factory=dict)
    # Days whose close came from the backup because Yahoo lacked them.
    filled: set[date] = field(default_factory=set)
    # Ex-dividend days Yahoo lists.
    dividends: set[date] = field(default_factory=set)


Closes = dict[str, SeriesCloses]


def sessions(market: Market, series: Iterable[Series], closes: Closes) -> list[date]:
    """The market's sessions: the days any of its series has a close for, in order."""
    days = {
        day
        for one in series
        if one.market is market
        for day in closes[one.symbol].closes
    }
    return sorted(days)


def _is_placeholder(row: pd.Series) -> bool:
    prices = [row.get(name) for name in ("Open", "High", "Low", "Close")]
    return row.get("Volume") == 0 and len({float(price) for price in prices}) == 1


def series_from_frame(
    market: Market, frame: pd.DataFrame, now: datetime
) -> SeriesCloses:
    """The closes and ex-dividend days of a Yahoo daily frame, without placeholder bars and
    without the bar of a session not ended at `now`."""
    found = SeriesCloses()
    if "Close" not in frame:
        return found
    for moment, row in frame.iterrows():
        day = pd.Timestamp(moment).to_pydatetime().astimezone(market.zone).date()
        if row.get("Dividends", 0) and not pd.isna(row.get("Dividends")):
            found.dividends.add(day)
        close = row.get("Close")
        if close is None or pd.isna(close) or _is_placeholder(row):
            continue
        if market.close_at(day) > now:
            continue
        found.closes[day] = float(close)
    return found


def _read_yahoo(symbol: str, start: date, end: date) -> pd.DataFrame:
    # Unadjusted closes, with the dividend days, and the days Yahoo lists without a close kept
    # (yfinance drops them by default).
    try:
        frame = yf.Ticker(symbol).history(
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            actions=True,
            keepna=True,
        )
    except Exception as error:
        # yfinance raises its own errors and its HTTP client's; any of them means the series
        # could not be read.
        raise ClosesError(f"{YAHOO} {symbol}: {error}") from error
    if frame.empty:
        # yfinance answers some failures with an empty frame instead of an error.
        raise ClosesError(f"{YAHOO} {symbol}: no daily data from {start} to {end}")
    return frame


def _read_backup(series: Series, start: date, end: date) -> dict[date, float]:
    assert series.backup is not None
    try:
        closes = finmind_closes(series.backup.id, start, end)
    except SourceError as error:
        raise ClosesError(str(error)) from error
    return {day: float(close) for day, close in closes.items()}


YahooReader = Callable[[str, date, date], pd.DataFrame]
BackupReader = Callable[[Series, date, date], dict[date, float]]


def read_closes(
    series: Sequence[Series],
    start: date,
    end: date,
    now: datetime,
    read_yahoo: YahooReader = _read_yahoo,
    read_backup: BackupReader = _read_backup,
) -> Closes:
    """Each series' closes from `start` to `end`: one Yahoo request a series, and one backup
    request for a series with a backup that lacks a session day of its market. Raises
    ClosesError when a source cannot be read."""
    closes: Closes = {
        one.symbol: series_from_frame(
            one.market, read_yahoo(one.symbol, start, end), now
        )
        for one in series
    }
    # The sessions as Yahoo alone gives them decide which series lack a day.
    yahoo_sessions = {
        one.market.code: sessions(one.market, series, closes) for one in series
    }
    for one in series:
        found = closes[one.symbol]
        lacking = any(
            day not in found.closes for day in yahoo_sessions[one.market.code]
        )
        if one.backup is None or not lacking:
            continue
        for day, close in read_backup(one, start, end).items():
            if day not in found.closes and one.market.close_at(day) <= now:
                found.closes[day] = close
                found.filled.add(day)
    return closes
