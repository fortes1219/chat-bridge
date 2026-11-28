"""The numbers a question's price lookups give, and the `<prices>` block the program reads.

Every number is the service's: a lookup's trend over its period, every trading day of a short
period, and each found event's rows on its trading day and after, lined up as the sample news
files' market sections are (`docs/truth_format.md` section 7). The total return and the largest
fall from a high are defined as ffn defines them.

An event is named by its file and event date with the numbers of its sections in `<sources>`, so
the only `[n]` in the block are those numbers. The block keeps every lookup's line; the days of
short periods, then the events' rows in the order the events were found, are added while the
whole block stays within its bound, and a line counts what was left out. A lookup that could not
be read is said in a fixed sentence naming its source; the source's own message goes to the
question's record only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from chat_bridge.price_history.closes import SeriesCloses
from chat_bridge.price_history.lookups import LeftOut, LeftOutReason, Lookup
from chat_bridge.price_history.markets import DayZero, MarketSeries, by_date, by_moment
from chat_bridge.price_history.moves import move, percent
from chat_bridge.price_history.reading import Reads
from chat_bridge.price_history.schemas import (
    MoveNotes,
    NotRead,
    NotReadReason,
    PriceDay,
    PriceEvent,
    PriceLookup,
    PriceLookups,
    PriceRow,
    PriceSource,
    PriceTrend,
)
from chat_bridge.strategy.compute import PRICE_TERMS_URL
from chat_bridge.strategy.prices import SOURCE_NAME
from chat_bridge.strategy.schemas import PriceSourceView

# A safety bound, not a tuned value: the largest block measured with every event kept was 23,632
# characters (6 holdings, 47 events).
BLOCK_BOUND = 30_000
# A period this short gets a row for every trading day.
DAYS_SHOWN = 10
# The lookups left out that the block names one by one; the rest are counted.
NAMED_LEFT_OUT = 10
NOT_A_NUMBER = "n/a"
OPEN, CLOSE = "<prices>", "</prices>"
INTRO = (
    "The app's numbers, from daily closes: Yahoo Finance, with FinMind for the Taiwan days "
    "Yahoo lacks. Closes are not adjusted for dividends; changes are in percent."
)
DAYS_INTRO = "Every trading day of a short period:"
DAYS_HEADER = (
    "| symbol | day | close | change from the trading day before |",
    "|---|---|---|---|",
)
EVENTS_INTRO = (
    "Events of the sources: D0 is the event's first trading day in that market. day: D0 against "
    "the trading day before it. next: the next trading day against D0. D+5: the fifth trading "
    "day after D0 against the trading day before D0."
)
EVENTS_HEADER = (
    "| symbol | D0 | D0 close | day | next | D+5 | notes |",
    "|---|---|---|---|---|---|---|",
)
SPLIT_FAILED = "No prices were looked up for this question: the split did not finish."
REASONS: dict[LeftOutReason, str] = {
    LeftOutReason.UNKNOWN_SYMBOL: "a symbol of no market the app reads",
    LeftOutReason.CASH: "cash has no prices",
    LeftOutReason.NOT_A_DATE: "not a date",
    LeftOutReason.START_AFTER_END: "starts after it ends",
    LeftOutReason.IN_THE_FUTURE: "ends after today",
    LeftOutReason.TOO_LONG: "longer than a year",
    LeftOutReason.TOO_MANY: "too many lookups",
}
SOURCE_NAMES: dict[PriceSource, str] = {"yahoo": SOURCE_NAME, "finmind": "FinMind"}
NOT_READ: dict[NotReadReason, str] = {
    "no_data": "had no daily closes for it",
    "unreadable": "could not be read",
}


@dataclass(frozen=True)
class FoundEvent:
    """A found file with an event: its date, its markets (the first is the event's), the moment
    it happened when the file gives one, and the numbers of its sections in `<sources>`."""

    file: str
    event_date: date
    markets: tuple[str, ...]
    moment: datetime | None
    numbers: tuple[int, ...]


@dataclass(frozen=True)
class Prices:
    view: PriceLookups
    block: str
    # Each symbol not read with its source's own message, for the record only.
    errors: dict[str, str]


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def trend(closes: Mapping[date, float], days: Sequence[date]) -> PriceTrend | None:
    """The trend over the trading days `days`, from the closes it has; None without one."""
    values = [(day, closes[day]) for day in days if day in closes]
    if not values:
        return None
    (first_day, first), (last_day, last) = values[0], values[-1]
    high_day, high = max(values, key=lambda value: value[1])
    low_day, low = min(values, key=lambda value: value[1])
    peak_day, peak = values[0]
    fall, fell = 0.0, None
    for day, close in values:
        if close > peak:
            peak_day, peak = day, close
        if close / peak - 1 < fall:
            fall, fell = close / peak - 1, (peak_day, day)
    change = percent(first, last)
    assert change is not None
    return PriceTrend(
        first_day=first_day,
        first_close=round(first, 2),
        last_day=last_day,
        last_close=round(last, 2),
        change=change,
        high_day=high_day,
        high=round(high, 2),
        low_day=low_day,
        low=round(low, 2),
        largest_fall=round(fall * 100, 2),
        fall_from=None if fell is None else fell[0],
        fall_to=None if fell is None else fell[1],
    )


def _days(
    closes: Mapping[date, float], sessions: Sequence[date], shown: Sequence[date]
) -> list[PriceDay]:
    rows: list[PriceDay] = []
    for day in shown:
        index = sessions.index(day)
        before = closes.get(sessions[index - 1]) if index > 0 else None
        rows.append(
            PriceDay(
                day=day,
                close=_rounded(closes.get(day)),
                change=percent(before, closes.get(day)),
            )
        )
    return rows


def lookup_views(lookups: Sequence[Lookup], reads: Reads) -> list[PriceLookup]:
    views: list[PriceLookup] = []
    for lookup in lookups:
        one = lookup.series
        read = reads.by_symbol[one.symbol]
        sessions = reads.sessions.get(one.market.code, [])
        period = [day for day in sessions if lookup.start <= day <= lookup.end]
        found = read.closes
        views.append(
            PriceLookup(
                symbol=one.symbol,
                name=one.name,
                start_date=lookup.start,
                end_date=lookup.end,
                read_at=read.read_at,
                stored=read.stored,
                sources=["yahoo", "finmind"] if found and found.filled else ["yahoo"],
                trend=None if found is None else trend(found.closes, period),
                days=[]
                if found is None or len(period) > DAYS_SHOWN
                else _days(found.closes, sessions, period),
                not_read=None
                if read.error is None
                else NotRead(source=read.error.source, reason=read.error.reason),
            )
        )
    return views


def _row(
    symbol: str, found: SeriesCloses, zero: DayZero, sessions: Sequence[date]
) -> PriceRow:
    moved = move(found, zero, sessions)
    return PriceRow(
        symbol=symbol,
        aligned=moved.aligned,
        d0=moved.session,
        close=_rounded(moved.close),
        day_change=percent(moved.before_close, moved.close),
        next_change=percent(moved.close, moved.after_close),
        fifth_change=percent(moved.before_close, moved.fifth_close),
        notes=MoveNotes(
            during=moved.during,
            missing=list(moved.missing),
            filled=list(moved.filled),
            dividends=list(moved.dividends),
        ),
    )


def event_rows(
    event: FoundEvent, lookups: Sequence[Lookup], reads: Reads, listed: MarketSeries
) -> list[PriceRow]:
    """The event's row for each series read whose lookup covers its date, once a series."""
    event_market = listed.market(event.markets[0]) if event.markets else None
    if event_market is None:
        return []
    rows: dict[str, PriceRow] = {}
    for lookup in lookups:
        one = lookup.series
        found = reads.by_symbol[one.symbol].closes
        if found is None or one.symbol in rows:
            continue
        if not lookup.start <= event.event_date <= lookup.end:
            continue
        sessions = reads.sessions.get(one.market.code, [])
        zero = (
            by_moment(one.market, event.moment, sessions)
            if event.moment is not None
            else by_date(one.market, event_market, event.event_date, sessions)
        )
        rows[one.symbol] = _row(one.symbol, found, zero, sessions)
    return list(rows.values())


def _close(value: float | None) -> str:
    return NOT_A_NUMBER if value is None else f"{value:.2f}"


def _change(value: float | None) -> str:
    return NOT_A_NUMBER if value is None else f"{value:+.2f}%"


def _lookup_line(view: PriceLookup) -> str:
    named = view.symbol if view.name == view.symbol else f"{view.symbol} ({view.name})"
    head = f"- {named}, {view.start_date} to {view.end_date}"
    if view.not_read is not None:
        source = SOURCE_NAMES[view.not_read.source]
        return f"{head}: not read: {source} {NOT_READ[view.not_read.reason]}"
    found = view.trend
    if found is None:
        return f"{head}: no trading day in the period"
    # A fall is zero or below, so it has no sign of its own to show.
    fall = f"{found.largest_fall:.2f}%"
    if found.fall_from is not None:
        fall += f" ({found.fall_from} to {found.fall_to})"
    return (
        f"{head}: first {found.first_day} {_close(found.first_close)}; "
        f"last {found.last_day} {_close(found.last_close)}; change {_change(found.change)}; "
        f"high {found.high_day} {_close(found.high)}; low {found.low_day} {_close(found.low)}; "
        f"largest fall from a high {fall}"
    )


def _notes(notes: MoveNotes, d0: date | None) -> str:
    if d0 is None:
        return "no trading day yet"
    said = ["the event came during D0's session"] if notes.during else []
    said += [f"no close for {day}" for day in notes.missing]
    said += [f"{day} from FinMind" for day in notes.filled]
    said += [f"ex-dividend {day}" for day in notes.dividends]
    return "; ".join(said)


def _row_line(row: PriceRow) -> str:
    cells = [
        row.symbol,
        NOT_A_NUMBER if row.d0 is None else row.d0.isoformat(),
        _close(row.close),
        _change(row.day_change),
        _change(row.next_change),
        _change(row.fifth_change),
        _notes(row.notes, row.d0),
    ]
    return "| " + " | ".join(cells) + " |"


def _event_lines(event: PriceEvent) -> list[str]:
    numbers = " ".join(f"[{number}]" for number in event.source_numbers)
    head = f"{event.file}, event date {event.event_date}, sources {numbers}"
    if event.same_as is not None:
        return [f"{head}: same rows as {event.same_as}"]
    return [f"{head}:", *(_row_line(row) for row in event.rows)]


def _not_looked_up(left_out: Sequence[LeftOut]) -> list[str]:
    """The lookups left out, the first few by name and the rest counted, so a split that lists
    hundreds cannot fill the block; the record keeps every one."""
    said = [
        f"{one.symbol} {one.start_date} to {one.end_date} ({REASONS[one.reason]})"
        for one in left_out
        if one.reason in REASONS
    ]
    if not said:
        return []
    more = len(said) - NAMED_LEFT_OUT
    tail = f"; and {more} more" if more > 0 else ""
    return [f"Not looked up: {'; '.join(said[:NAMED_LEFT_OUT])}{tail}."]


def _day_lines(view: PriceLookup) -> list[str]:
    return [
        f"| {view.symbol} | {day.day} | {_close(day.close)} | {_change(day.change)} |"
        for day in view.days
    ]


def _text(
    head: list[str],
    days: list[list[str]],
    events: list[list[str]],
    days_left: int,
    events_left: int,
) -> str:
    lines = [OPEN, *head]
    if days:
        lines += ["", DAYS_INTRO, *DAYS_HEADER, *(line for one in days for line in one)]
    if events:
        lines += [
            "",
            EVENTS_INTRO,
            *EVENTS_HEADER,
            *(line for one in events for line in one),
        ]
    if days_left:
        lines.append(
            f"{days_left} trading days' rows were left out to keep this block short."
        )
    if events_left:
        lines.append(
            f"{events_left} more events' rows were left out to keep this block short."
        )
    return "\n".join([*lines, CLOSE])


def _within(groups: list[list[str]], used: int) -> tuple[int, int]:
    """How many of the groups, from the first, fit in the bound after `used` characters, and the
    characters used then."""
    kept = 0
    for group in groups:
        size = sum(len(line) + 1 for line in group)
        if used + size > BLOCK_BOUND:
            break
        kept += 1
        used += size
    return kept, used


def _shared(events: list[PriceEvent]) -> list[PriceEvent]:
    """Each event whose rows equal an earlier one's, naming that event's file instead."""
    first: dict[tuple[str, ...], str] = {}
    shared: list[PriceEvent] = []
    for event in events:
        rows = tuple(_row_line(row) for row in event.rows)
        earlier = first.setdefault(rows, event.file)
        if earlier == event.file:
            shared.append(event)
        else:
            shared.append(event.model_copy(update={"rows": [], "same_as": earlier}))
    return shared


def prices(
    lookups: Sequence[Lookup],
    left_out: Sequence[LeftOut],
    reads: Reads,
    found: Sequence[FoundEvent],
    listed: MarketSeries,
) -> Prices:
    """The lookups' numbers for the page and the block for the program."""
    views = lookup_views(lookups, reads)
    head = [INTRO, "", "Lookups:", *(_lookup_line(view) for view in views)]
    head += _not_looked_up(left_out)
    events = _shared(
        [
            PriceEvent(
                file=event.file,
                event_date=event.event_date,
                source_numbers=list(event.numbers),
                rows=rows,
            )
            for event in found
            if (rows := event_rows(event, lookups, reads, listed))
        ]
    )
    # Every lookup's line is kept. Then each short period's days, whole, and each event's rows,
    # in order, while the block stays within the bound: the room left is counted on the block
    # with both headers and both counts, so what is kept always fits.
    with_days = [view for view in views if view.days]
    day_groups = [_day_lines(view) for view in with_days]
    event_groups = [_event_lines(event) for event in events]
    room = len(_text(head, [[]], [[]], len(with_days) * DAYS_SHOWN, len(events)))
    days_kept, room = _within(day_groups, room)
    events_kept, _ = _within(event_groups, room)
    dropped = {id(view) for view in with_days[days_kept:]}
    days_left = sum(len(view.days) for view in with_days[days_kept:])
    # The kept events are the first ones, so an event that names an earlier one's rows names a
    # kept event.
    kept = events[:events_kept]
    view = PriceLookups(
        lookups=[
            one.model_copy(update={"days": []}) if id(one) in dropped else one
            for one in views
        ],
        events=kept,
        days_left_out=days_left,
        events_left_out=len(events) - events_kept,
        source=PriceSourceView(name=SOURCE_NAME, terms_url=PRICE_TERMS_URL),
    )
    text = _text(
        head,
        day_groups[:days_kept],
        event_groups[:events_kept],
        days_left,
        len(events) - events_kept,
    )
    errors = {
        symbol: str(read.error)
        for symbol, read in reads.by_symbol.items()
        if read.error is not None
    }
    return Prices(view, text, errors)


def split_failed() -> str:
    """The block of a question whose split did not finish: nothing was looked up."""
    return "\n".join([OPEN, SPLIT_FAILED, CLOSE])
