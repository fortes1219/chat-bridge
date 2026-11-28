"""The daily closes of a set of series over a span.

Yahoo's daily series is the first source; a day it lacks of a series with a backup comes from
that backup (FinMind for the Taiwan series). A market's sessions are the days any of its series
closed on. A bar Yahoo adds with no volume and the same open, high, low and close is its
placeholder for a day without trading, not a session; the bar of a session that has not ended
when the data is read is its latest price, not a close, and is left out.

The closes stay the floats Yahoo gives, unadjusted for dividends, so a change is worked out on the
same numbers as the sample files' market sections and the same data gives the same numbers.

The series are read at once, each in its own thread, and every request has the time limit of the
service's other daily reads, so one source that does not answer holds the rest up for at most
that limit. The first Yahoo request goes alone: yfinance makes its cache databases on its first
request in a process without a lock, and requests that start together then fail with "database
is locked" (measured on a fresh container: one series of nine).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Literal, TypeVar

import pandas as pd
import yfinance as yf

from chat_bridge.price_history.markets import Market, Series
from chat_bridge.strategy.taiwan_sources import (
    TIMEOUT_SECONDS,
    SourceError,
    finmind_closes,
)

# Where each source is named in a news file's `sources` and in the notes of its moves.
YAHOO = "Yahoo"
BACKUP_NAMES = {"finmind": "FinMind"}
# More threads than series would wait idle; more than this would only queue at the sources.
MOST_THREADS = 16


Source = Literal["yahoo", "finmind"]
# Why a series was not read: the source answered with no daily data for it, or did not answer
# (an error, or no answer within the time limit).
Reason = Literal["no_data", "unreadable"]


class ClosesError(Exception):
    """A source of daily closes could not be read. The message names it, for logs and records;
    the source and the reason are for the page and the answering program to say it in their own
    words."""

    def __init__(
        self, message: str, *, source: Source = "yahoo", reason: Reason = "unreadable"
    ) -> None:
        super().__init__(message)
        self.source: Source = source
        self.reason: Reason = reason


@dataclass
class SeriesCloses:
    closes: dict[date, float] = field(default_factory=dict)
    # Days whose close came from the backup because Yahoo lacked them.
    filled: set[date] = field(default_factory=set)
    # Ex-dividend days Yahoo lists.
    dividends: set[date] = field(default_factory=set)


Closes = dict[str, SeriesCloses]


def sessions(market: Market, series: Iterable[Series], closes: Closes) -> list[date]:
    """The market's sessions: the days any of its series has a close for, in order. A series
    with no closes in `closes` adds none."""
    days = {
        day
        for one in series
        if one.market is market and one.symbol in closes
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


def yahoo_daily(symbol: str, start: date, end: date) -> pd.DataFrame:
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
            timeout=TIMEOUT_SECONDS,
        )
    except Exception as error:
        # yfinance raises its own errors and its HTTP client's; any of them means the series
        # could not be read.
        raise ClosesError(f"{YAHOO} {symbol}: {error}") from error
    if frame.empty:
        # yfinance answers some failures, and a symbol it does not know, with an empty frame
        # instead of an error.
        raise ClosesError(
            f"{YAHOO} {symbol}: no daily data from {start} to {end}", reason="no_data"
        )
    return frame


def backup_daily(series: Series, start: date, end: date) -> dict[date, float]:
    assert series.backup is not None
    try:
        closes = finmind_closes(series.backup.id, start, end)
    except SourceError as error:
        raise ClosesError(str(error), source="finmind") from error
    return {day: float(close) for day, close in closes.items()}


YahooReader = Callable[[str, date, date], pd.DataFrame]
BackupReader = Callable[[Series, date, date], dict[date, float]]
Read = SeriesCloses | ClosesError


T = TypeVar("T")
R = TypeVar("R")


def _each(items: Sequence[T], work: Callable[[T], R]) -> list[R | ClosesError]:
    """`work` on every item at once, each in its own thread; a ClosesError is returned, not
    raised, so one item that fails does not end the others."""

    def guarded(item: T) -> R | ClosesError:
        try:
            return work(item)
        except ClosesError as error:
            return error

    if not items:
        return []
    with ThreadPoolExecutor(max_workers=min(len(items), MOST_THREADS)) as pool:
        return list(pool.map(guarded, items))


def read_each(
    series: Sequence[Series],
    start: date,
    end: date,
    now: datetime,
    read_yahoo: YahooReader = yahoo_daily,
    read_backup: BackupReader = backup_daily,
) -> dict[str, Read]:
    """Each series' closes from `start` to `end`, or why they could not be read: one Yahoo
    request a series, and one backup request for a series with a backup that lacks a session day
    of its market. A series whose backup cannot be read is not read either."""

    def yahoo(one: Series) -> pd.DataFrame:
        return read_yahoo(one.symbol, start, end)

    frames = [*_each(series[:1], yahoo), *_each(series[1:], yahoo)]
    read: dict[str, Read] = {
        one.symbol: frame
        if isinstance(frame, ClosesError)
        else series_from_frame(one.market, frame, now)
        for one, frame in zip(series, frames, strict=True)
    }
    found: Closes = {
        symbol: closes
        for symbol, closes in read.items()
        if isinstance(closes, SeriesCloses)
    }
    # The sessions as Yahoo alone gives them decide which series lack a day.
    yahoo_sessions = {
        one.market.code: sessions(one.market, series, found) for one in series
    }
    lacking = [
        one
        for one in series
        if one.backup is not None
        and one.symbol in found
        and any(
            day not in found[one.symbol].closes
            for day in yahoo_sessions[one.market.code]
        )
    ]
    backups = _each(lacking, lambda one: read_backup(one, start, end))
    for one, backup in zip(lacking, backups, strict=True):
        if isinstance(backup, ClosesError):
            read[one.symbol] = backup
            continue
        closes = found[one.symbol]
        for day, close in backup.items():
            if day not in closes.closes and one.market.close_at(day) <= now:
                closes.closes[day] = close
                closes.filled.add(day)
    return read


def read_closes(
    series: Sequence[Series],
    start: date,
    end: date,
    now: datetime,
    read_yahoo: YahooReader = yahoo_daily,
    read_backup: BackupReader = backup_daily,
) -> Closes:
    """Each series' closes, as `read_each` reads them. Raises ClosesError, for the first series
    listed that could not be read, when one could not."""
    read = read_each(series, start, end, now, read_yahoo, read_backup)
    for one in series:
        failed = read[one.symbol]
        if isinstance(failed, ClosesError):
            raise failed
    return {
        symbol: closes
        for symbol, closes in read.items()
        if isinstance(closes, SeriesCloses)
    }
