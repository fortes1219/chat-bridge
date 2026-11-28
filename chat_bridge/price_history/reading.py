"""The closes a question's lookups need: from the day's store, or read from the sources.

The trading days of a market are the days its listed series closed on, as for the sample news
files' market sections, so every series of a market is read with the market's listed series and
the same read serves them all. A market whose stored reads do not all serve the lookups, or come
from different reads, is read again whole.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from chat_bridge.price_history import day_store
from chat_bridge.price_history.closes import (
    BackupReader,
    ClosesError,
    SeriesCloses,
    YahooReader,
    backup_daily,
    read_each,
    sessions,
    yahoo_daily,
)
from chat_bridge.price_history.lookups import Lookup
from chat_bridge.price_history.markets import Market, MarketSeries, Series

logger = logging.getLogger(__name__)

# Days read before a period, so the two trading days before an event at its start are read
# across a long holiday; the same span the market sections were read with.
SPAN_DAYS = 21


@dataclass(frozen=True)
class SymbolRead:
    series: Series
    closes: SeriesCloses | None
    # Why the closes could not be read; None when they were.
    error: ClosesError | None
    # Whether the closes came from the day's store rather than the sources.
    stored: bool
    read_at: datetime | None


@dataclass(frozen=True)
class Reads:
    by_symbol: dict[str, SymbolRead]
    # Each market's trading days, by market code.
    sessions: dict[str, list[date]]


@dataclass(frozen=True)
class _Group:
    market: Market
    series: tuple[Series, ...]
    start: date


def _groups(lookups: Sequence[Lookup], listed: MarketSeries) -> list[_Group]:
    groups: list[_Group] = []
    markets = list(dict.fromkeys(lookup.series.market for lookup in lookups))
    for market in markets:
        own = [lookup for lookup in lookups if lookup.series.market is market]
        series = {one.symbol: one for one in listed.of_market(market)}
        for lookup in own:
            series.setdefault(lookup.series.symbol, lookup.series)
        start = min(lookup.start for lookup in own) - timedelta(days=SPAN_DAYS)
        groups.append(_Group(market, tuple(series.values()), start))
    return groups


def _served(
    group: _Group, now: datetime, under: Path | None
) -> dict[str, day_store.Stored] | None:
    """The group's stored reads when they all serve it and come from one read."""
    stored = {one.symbol: day_store.load(one.symbol, under) for one in group.series}
    kept = {symbol: read for symbol, read in stored.items() if read is not None}
    if len(kept) != len(stored) or not all(
        day_store.serves(read, group.start, now) for read in kept.values()
    ):
        return None
    if len({read.read_at for read in kept.values()}) != 1:
        return None
    return kept


def read_for(
    lookups: Sequence[Lookup],
    listed: MarketSeries,
    now: datetime,
    *,
    read_yahoo: YahooReader = yahoo_daily,
    read_backup: BackupReader = backup_daily,
    under: Path | None = None,
) -> Reads:
    """The closes of every series the lookups need, each market from one read. Never raises for
    a source that cannot be read: the series says why."""
    by_symbol: dict[str, SymbolRead] = {}
    stale: list[_Group] = []
    for group in _groups(lookups, listed):
        served = _served(group, now, under)
        if served is None:
            stale.append(group)
            continue
        for one in group.series:
            kept = served[one.symbol]
            by_symbol[one.symbol] = SymbolRead(
                one, kept.closes, None, True, kept.read_at
            )
    if stale:
        start = min(group.start for group in stale)
        # A session that has not ended when the data is read is left out, so the span may run
        # past the day in every market's own time.
        end = now.date() + timedelta(days=1)
        series = [one for group in stale for one in group.series]
        read = read_each(series, start, end, now, read_yahoo, read_backup)
        for one in series:
            found = read[one.symbol]
            if isinstance(found, ClosesError):
                by_symbol[one.symbol] = SymbolRead(one, None, found, False, None)
                continue
            try:
                day_store.save(one.symbol, start, now, found, under)
            except OSError as error:
                logger.warning("Could not keep the read of %s: %s", one.symbol, error)
            by_symbol[one.symbol] = SymbolRead(one, found, None, False, now)
    days = {
        group.market.code: sessions(
            group.market,
            group.series,
            {
                symbol: read.closes
                for symbol, read in by_symbol.items()
                if read.closes is not None
            },
        )
        for group in _groups(lookups, listed)
    }
    return Reads(by_symbol, days)
