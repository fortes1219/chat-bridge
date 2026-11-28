"""A series' moves on an event's trading day and after, from its daily closes.

These are the values of a row of the sample news files' section 當日與之後的行情
(`docs/truth_format.md` section 7): day 0 and the trading days around it, their closes, and what the
notes of the row say. A change is worked out from two closes as that section works it out, so the
same closes give the same numbers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from chat_bridge.price_history.closes import SeriesCloses
from chat_bridge.price_history.markets import DayZero


@dataclass(frozen=True)
class Move:
    aligned: date
    # Day 0; None when the data has no session on or after the aligned day yet.
    session: date | None
    # The event came while day 0's session was open.
    during: bool = False
    before_2: date | None = None
    before: date | None = None
    after: date | None = None
    fifth: date | None = None
    before_2_close: float | None = None
    before_close: float | None = None
    close: float | None = None
    after_close: float | None = None
    fifth_close: float | None = None
    # The sessions from day −2 to day +5 the series has no close for, those whose close came
    # from the backup, and the ex-dividend days among them, each in order.
    missing: tuple[date, ...] = ()
    filled: tuple[date, ...] = ()
    dividends: tuple[date, ...] = ()
    # Whether a close shown (day −2, −1, 0, +1 or +5) came from the backup.
    uses_backup: bool = False


def change(before: float | None, after: float | None) -> float | None:
    """The change from one close to another, as a fraction; None when either is missing."""
    if before is None or after is None:
        return None
    return after / before - 1


def percent(before: float | None, after: float | None) -> float | None:
    """The change in percent, rounded as the section writes it: a change that lands on a half
    rounds as the section's text does (2415 against 2400 is +0.63, not +0.62)."""
    fraction = change(before, after)
    return None if fraction is None else round(fraction * 100, 2)


def _at(days: Sequence[date], index: int) -> date | None:
    return days[index] if 0 <= index < len(days) else None


def move(found: SeriesCloses, zero: DayZero, days: Sequence[date]) -> Move:
    """The series' move for an event placed at `zero`, on its market's sessions `days`."""
    if zero.session is None:
        return Move(zero.aligned, None)
    index = days.index(zero.session)
    before_2, before, after, fifth = (
        _at(days, index + offset) for offset in (-2, -1, 1, 5)
    )
    # The sessions from day −2 to day +5 that the data has.
    window = days[max(index - 2, 0) : index + 6]

    def close(day: date | None) -> float | None:
        return None if day is None else found.closes.get(day)

    shown = (before_2, before, zero.session, after, fifth)
    return Move(
        aligned=zero.aligned,
        session=zero.session,
        during=zero.during,
        before_2=before_2,
        before=before,
        after=after,
        fifth=fifth,
        before_2_close=close(before_2),
        before_close=close(before),
        close=close(zero.session),
        after_close=close(after),
        fifth_close=close(fifth),
        missing=tuple(day for day in window if day not in found.closes),
        filled=tuple(day for day in window if day in found.filled),
        dividends=tuple(
            day for day in sorted(found.dividends) if window[0] <= day <= window[-1]
        ),
        uses_backup=any(day in found.filled for day in shown),
    )
