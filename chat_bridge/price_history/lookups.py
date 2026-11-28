"""The price lookups a question's split names, checked before anything is read.

What comes back from the split is a model's writing, so each lookup is checked here: a symbol the
service can place in a market, real dates, a period that has begun and is not too long. A lookup
that fails a check is left out with the reason, and the rest go on.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

from chat_bridge.price_history.markets import Backup, MarketSeries, Series
from chat_bridge.strategy.models import CASH
from chat_bridge.strategy.store import market_of
from chat_bridge.strategy.taiwan_sources import code_of

# Safety bounds, not tuned values: a person keeps at most 30 holdings and the sample lists 9
# series, and a year covers "the last half year" with room.
MOST_LOOKUPS = 40
LONGEST_PERIOD_DAYS = 366
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
# The backup of a Taiwan listing the series file does not list: FinMind's daily closes.
TAIWAN_BACKUP = "finmind"


class Asked(Protocol):
    """A lookup as the split's reply names it."""

    symbol: str
    start_date: str
    end_date: str


class LeftOutReason(StrEnum):
    UNKNOWN_SYMBOL = "unknown_symbol"  # in no market the service keeps
    CASH = "cash"  # the cash holding, which has no prices
    NOT_A_DATE = "not_a_date"
    START_AFTER_END = "start_after_end"
    IN_THE_FUTURE = "in_the_future"
    TOO_LONG = "too_long"
    REPEATED = "repeated"
    TOO_MANY = "too_many"


@dataclass(frozen=True)
class Lookup:
    series: Series
    start: date
    end: date


@dataclass(frozen=True)
class LeftOut:
    symbol: str
    start_date: str
    end_date: str
    reason: LeftOutReason


@dataclass(frozen=True)
class Checked:
    kept: tuple[Lookup, ...]
    left_out: tuple[LeftOut, ...]


def place(symbol: str, listed: MarketSeries, names: Mapping[str, str]) -> Series | None:
    """The series of a symbol: a listed series, or a Taiwan or US listing as the holdings take
    them, named as the person's holding when it is one. None for any other symbol."""
    known = next((one for one in listed.series if one.symbol == symbol), None)
    if known is not None:
        return known
    code = market_of(symbol)
    market = None if code is None else listed.market(code)
    if code is None or market is None:
        return None
    backup = Backup(TAIWAN_BACKUP, code_of(symbol)) if code == "TW" else None
    return Series(symbol, names.get(symbol, symbol), market, backup)


def _day(text: str) -> date | None:
    if not DATE_PATTERN.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _lookup(
    one: Asked, today: date, listed: MarketSeries, names: Mapping[str, str]
) -> Lookup | LeftOutReason:
    """The lookup asked for, or why it cannot be run."""
    symbol = one.symbol.strip().upper()
    if symbol == CASH:
        return LeftOutReason.CASH
    series = place(symbol, listed, names)
    if series is None:
        return LeftOutReason.UNKNOWN_SYMBOL
    start, end = _day(one.start_date.strip()), _day(one.end_date.strip())
    if start is None or end is None:
        return LeftOutReason.NOT_A_DATE
    if start > end:
        return LeftOutReason.START_AFTER_END
    if end > today:
        return LeftOutReason.IN_THE_FUTURE
    if (end - start).days + 1 > LONGEST_PERIOD_DAYS:
        return LeftOutReason.TOO_LONG
    return Lookup(series, start, end)


def check(
    asked: Sequence[Asked],
    today: date,
    listed: MarketSeries,
    names: Mapping[str, str],
) -> Checked:
    """The lookups to run, in the order listed, at most MOST_LOOKUPS, and those left out with
    why. `names` names the person's holdings by symbol."""
    kept: list[Lookup] = []
    left_out: list[LeftOut] = []
    for one in asked:
        found = _lookup(one, today, listed, names)
        if isinstance(found, Lookup) and found in kept:
            found = LeftOutReason.REPEATED
        elif isinstance(found, Lookup) and len(kept) == MOST_LOOKUPS:
            found = LeftOutReason.TOO_MANY
        if isinstance(found, Lookup):
            kept.append(found)
        else:
            left_out.append(LeftOut(one.symbol, one.start_date, one.end_date, found))
    return Checked(tuple(kept), tuple(left_out))
