"""Each series' recent trading days, and the previous close of a day as a quote screen gives it.

The previous close of a day is the close of the trading day before it. On a Taiwan ex-dividend or
ex-rights day it is the exchange's reference price instead: the close less the dividend, by the
exchange's reckoning. A trading day a source lists without a close stays missing, and the sources
say nothing of a day after the one they were read on, as the trading day before it may be one
they did not have yet: an earlier close never stands in, as that would make a move of two days
look like one day's.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from decimal import Decimal
from zoneinfo import ZoneInfo

# Taiwan keeps one offset all year; the US exchanges' zone has daylight saving.
TAIPEI = timezone(timedelta(hours=8))
NEW_YORK = ZoneInfo("America/New_York")
# Yahoo dates a currency pair's daily values by the day in London (TWD=X: Europe/London, each
# value at 00:00 there).
LONDON = ZoneInfo("Europe/London")
TAIWAN_SUFFIXES = (".TW", ".TWO")
CURRENCY_SUFFIX = "=X"
# The end of the US exchanges' regular session, in New York. Yahoo's stream measures a price after
# it, in the evening and overnight, from that session's close (spec 006 research).
US_SESSION_END = time(16)


def is_taiwan(symbol: str) -> bool:
    return symbol.endswith(TAIWAN_SUFFIXES)


def zone_of(symbol: str) -> tzinfo:
    """The zone the series' trading days are counted in, as Yahoo dates its daily values."""
    if is_taiwan(symbol):
        return TAIPEI
    if symbol.endswith(CURRENCY_SUFFIX):
        return LONDON
    return NEW_YORK


def trading_day(symbol: str, moment: datetime) -> date:
    """The day `moment` falls on where the series trades."""
    return moment.astimezone(zone_of(symbol)).date()


def change_day(symbol: str, moment: datetime) -> date:
    """The day whose previous close a price at `moment` is measured from: its trading day, except
    that a US price from the end of the regular session on counts toward the next day, so every
    price outside the session is measured from the last regular close and nothing moves at
    midnight in New York. On an early-close day, a price between that close and 16:00 is still
    measured from the day before's close. A currency pair trades round the clock: its day is
    the day in London."""
    zone = zone_of(symbol)
    local = moment.astimezone(zone)
    if zone is not NEW_YORK or local.time() < US_SESSION_END:
        return local.date()
    return local.date() + timedelta(days=1)


@dataclass(frozen=True)
class History:
    """What the sources gave of one series' recent days."""

    # The day the sources were read on, where the series trades. Its close may be a price from
    # while it traded, and a later day's previous close was not known then.
    read_on: date
    closes: dict[date, Decimal] = field(default_factory=dict)
    # Trading days a source listed without a close.
    missing: frozenset[date] = frozenset()
    # A day's previous close as an exchange gives it: the reference price of an ex-dividend or
    # ex-rights day, or a day's close less its change.
    given: dict[date, Decimal] = field(default_factory=dict)
    # Announced ex-dividend or ex-rights days: the cash dividend when it is the only one and its
    # amount is announced, else None, as the reference price cannot be worked out.
    dividends: dict[date, Decimal | None] = field(default_factory=dict)
    # The OTC market's reference price for the first trading day after the given day.
    next_reference: tuple[date, Decimal] | None = None

    def merged(self, other: History) -> History:
        """This history with what `other` adds; `other` wins where both give a day.

        Once a later read is in, the value an earlier read gave of the day it was made on is no
        close, as it may be a price from while that day traded: the day stays missing unless a
        read gives its close.
        """
        read_on = max(self.read_on, other.read_on)
        closes: dict[date, Decimal] = {}
        missing = set(self.missing | other.missing)
        for history in (self, other):
            for day, close in history.closes.items():
                if history.read_on < read_on and day >= history.read_on:
                    missing.add(day)
                else:
                    closes[day] = close
        return History(
            read_on=read_on,
            closes=closes,
            missing=frozenset(missing - closes.keys()),
            given={**self.given, **other.given},
            dividends={**self.dividends, **other.dividends},
            next_reference=other.next_reference or self.next_reference,
        )

    @property
    def latest(self) -> date | None:
        return max(self.closes) if self.closes else None

    def previous_close(self, day: date) -> Decimal | None:
        """The previous close of `day`; None when the sources do not give it."""
        if day in self.given:
            return self.given[day]
        if day > self.read_on:
            return None
        last = max(
            (known for known in (*self.closes, *self.missing) if known < day),
            default=None,
        )
        if self.next_reference is not None:
            after, price = self.next_reference
            if after < day and (last is None or last <= after):
                return price
        if last is None or last in self.missing:
            return None
        close = self.closes[last]
        if day not in self.dividends:
            return close
        cash = self.dividends[day]
        return None if cash is None else close - cash
