"""What a question's price lookups gave, as the page shows it and the record keeps it.

The numbers are rounded as the model reads them: closes to two decimals, changes in percent to
two decimals.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from chat_bridge.strategy.schemas import PriceSourceView

PriceSource = Literal["yahoo", "finmind"]
NotReadReason = Literal["no_data", "unreadable"]


class NotRead(BaseModel):
    """Why a lookup's closes were not read, for a page to say in its language: the source that
    failed, and whether it had no daily data for the symbol or did not answer. The source's own
    message stays in the question's record."""

    source: PriceSource
    reason: NotReadReason


class PriceTrend(BaseModel):
    """A lookup's period: its first and last trading day, the change between them, the highest
    and lowest close, and the largest fall from a high."""

    first_day: date
    first_close: float
    last_day: date
    last_close: float
    change: float
    high_day: date
    high: float
    low_day: date
    low: float
    # Zero or below; the high it fell from and the day it reached its low, none without a fall.
    largest_fall: float
    fall_from: date | None = None
    fall_to: date | None = None


class PriceDay(BaseModel):
    day: date
    close: float | None
    # Against the market's trading day before it.
    change: float | None


class MoveNotes(BaseModel):
    """What a row's notes say: the event came during day 0's session; the trading days from day
    −2 to day +5 the series has no close for, those whose close came from FinMind, and the
    ex-dividend days among them."""

    during: bool = False
    missing: list[date] = Field(default_factory=list)
    filled: list[date] = Field(default_factory=list)
    dividends: list[date] = Field(default_factory=list)


class PriceRow(BaseModel):
    """A series on an event's trading day (D0) and after."""

    symbol: str
    aligned: date
    # None when the data has no trading day on or after the aligned day yet.
    d0: date | None
    close: float | None
    # D0 against the trading day before it; the next trading day against D0; the fifth trading
    # day after D0 against the trading day before D0.
    day_change: float | None
    next_change: float | None
    fifth_change: float | None
    notes: MoveNotes


class PriceLookup(BaseModel):
    symbol: str
    name: str
    start_date: date
    end_date: date
    # When its closes were read, and whether from the day's store; none when they were not read.
    read_at: datetime | None
    stored: bool
    sources: list[PriceSource]
    # None when it was not read, or has no trading day in its period.
    trend: PriceTrend | None
    # Every trading day of a period of at most ten.
    days: list[PriceDay]
    # Why its closes could not be read.
    not_read: NotRead | None = None


class PriceEvent(BaseModel):
    """A found event's rows, named by its file and the numbers of its sources."""

    file: str
    event_date: date
    source_numbers: list[int]
    rows: list[PriceRow]
    # The file of an earlier event whose rows are the same, given instead of repeating them.
    same_as: str | None = None


class PriceLookups(BaseModel):
    lookups: list[PriceLookup]
    events: list[PriceEvent]
    # Rows left out to keep the block within its bound: the trading days of short periods, and
    # the events' rows.
    days_left_out: int = 0
    events_left_out: int = 0
    # Where the closes come from and its terms, as the strategy panel names them.
    source: PriceSourceView
