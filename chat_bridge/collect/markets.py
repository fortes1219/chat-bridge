"""The markets and series a news file's market moves follow, and each market's day 0.

The list is data (`data/market_series.json`), so the series can change without changing the
program. Day 0 of a market is the first of its sessions whose close is at or after the moment of
the event; a news file without that moment is aligned by its date, as the earlier files were.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError

MARKET_SERIES_FILE = PROJECT_ROOT / "data" / "market_series.json"


class MarketSeriesFileError(LocalSetupError):
    """The markets and series file is missing or not the shape. The message says which."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _MarketEntry(_Strict):
    code: str = Field(min_length=1)
    label: str = Field(min_length=1)
    zone: str
    opens: str
    closes: str


class _Backup(_Strict):
    source: Literal["finmind"]
    id: str = Field(min_length=1)


class _SeriesEntry(_Strict):
    symbol: str = Field(min_length=1)
    name: str = Field(min_length=1)
    market: str
    backup: _Backup | None = None


class _MarketSeriesFile(_Strict):
    about: str
    markets: list[_MarketEntry] = Field(min_length=1)
    series: list[_SeriesEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _known_markets(self) -> _MarketSeriesFile:
        codes = [market.code for market in self.markets]
        if len(set(codes)) != len(codes):
            raise ValueError("a market code is listed twice")
        symbols = [series.symbol for series in self.series]
        if len(set(symbols)) != len(symbols):
            raise ValueError("a series is listed twice")
        unknown = [
            series.symbol for series in self.series if series.market not in codes
        ]
        if unknown:
            raise ValueError(f"series of no listed market: {', '.join(unknown)}")
        return self


@dataclass(frozen=True)
class Market:
    code: str
    # How the section's first line names the market's series ("台股").
    label: str
    zone: ZoneInfo
    opens: time
    closes: time

    def open_at(self, day: date) -> datetime:
        return datetime.combine(day, self.opens, self.zone)

    def close_at(self, day: date) -> datetime:
        return datetime.combine(day, self.closes, self.zone)


@dataclass(frozen=True)
class Backup:
    source: str
    id: str


@dataclass(frozen=True)
class Series:
    symbol: str
    name: str
    market: Market
    backup: Backup | None


@dataclass(frozen=True)
class MarketSeries:
    markets: tuple[Market, ...]
    series: tuple[Series, ...]

    def market(self, code: str) -> Market | None:
        return next((market for market in self.markets if market.code == code), None)


def _market(entry: _MarketEntry) -> Market:
    try:
        zone = ZoneInfo(entry.zone)
        opens, closes = (
            time.fromisoformat(entry.opens),
            time.fromisoformat(entry.closes),
        )
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"market {entry.code}: {error}") from error
    if opens >= closes:
        raise ValueError(f"market {entry.code} closes before it opens")
    return Market(entry.code, entry.label, zone, opens, closes)


@cache
def market_series(path: Path = MARKET_SERIES_FILE) -> MarketSeries:
    """The markets and series, read and checked once. Raises MarketSeriesFileError."""
    try:
        parsed = _MarketSeriesFile.model_validate_json(path.read_text(encoding="utf-8"))
        markets = {entry.code: _market(entry) for entry in parsed.markets}
    except (OSError, ValidationError, ValueError) as error:
        raise MarketSeriesFileError(f"{path.name}: {error}") from error
    series = tuple(
        Series(
            entry.symbol,
            entry.name,
            markets[entry.market],
            None
            if entry.backup is None
            else Backup(entry.backup.source, entry.backup.id),
        )
        for entry in parsed.series
    )
    return MarketSeries(tuple(markets.values()), series)


@dataclass(frozen=True)
class DayZero:
    """Where a market's series are aligned: the day the event is placed on, and its first session
    on or after it (None when the data has no such session yet)."""

    aligned: date
    session: date | None
    # The event came while that session was open, so its change includes the move before it.
    during: bool = False


def by_moment(market: Market, moment: datetime, sessions: Sequence[date]) -> DayZero:
    """Day 0: the first session whose close is at or after `moment`. `sessions` are sorted."""
    session = next((day for day in sessions if market.close_at(day) >= moment), None)
    # At the close itself (a market day's own close) the session is over, not under way.
    during = session is not None and market.open_at(session) < moment < market.close_at(
        session
    )
    return DayZero(moment.astimezone(market.zone).date(), session, during)


def aligned_date(market: Market, event_market: Market, event_date: date) -> date:
    """The day a market is aligned to by date: the event's date, or the next day when that
    market's session of the date closes before the event market's session of the date opens
    (Taiwan closes before New York opens, so a US event reaches Taiwan the next day)."""
    if market.close_at(event_date) < event_market.open_at(event_date):
        return event_date + timedelta(days=1)
    return event_date


def by_date(
    market: Market, event_market: Market, event_date: date, sessions: Sequence[date]
) -> DayZero:
    """Day 0 by the date rule: the first session on or after the aligned day."""
    aligned = aligned_date(market, event_market, event_date)
    return DayZero(aligned, next((day for day in sessions if day >= aligned), None))
