"""The section 「當日與之後的行情」 of a news file: one row a series, from the daily closes.

The columns, the notes and the first line are those of `docs/truth_format.md` section 7, so a
file aligned by date gets back the text it was written with when the closes are the same.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from chat_bridge.collect.closes import BACKUP_NAMES, Closes, SeriesCloses, sessions
from chat_bridge.collect.markets import (
    DayZero,
    Market,
    MarketSeries,
    Series,
    by_date,
    by_moment,
)

HEADING = "當日與之後的行情"
NO_DATA = "沒有資料"
HEADER = (
    "| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | "
    "次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |"
)
RULE = "|---|---|---|---|---|---|---|---|---|---|---|"
NOT_YET = "資料還沒有到這一天"
DURING = "事件發生在 D0 這一盤的交易時間內，當日% 含事件之前的走勢"
YAHOO_SOURCE_ID = "d1"
BACKUP_SOURCE_ID = "d2"


@dataclass(frozen=True)
class Event:
    """What the section needs from a news file's front matter."""

    event_date: date
    # The market of the event: the first of the file's `markets`.
    market: Market
    # When the event happened or was made public, with its offset; None aligns by date.
    moment: datetime | None


@dataclass(frozen=True)
class Section:
    lines: tuple[str, ...]
    # Whether a cell took a day from a series' backup, so the backup is a data source.
    uses_backup: bool


def _percent(before: float | None, after: float | None) -> str:
    if before is None or after is None:
        return NO_DATA
    # Worked out as the earlier sections were: the same closes give the same text, down to a
    # change that lands on a half (2415 against 2400 is +0.63%, not +0.62%).
    return f"{(after / before - 1) * 100:+.2f}%"


def _close(value: float | None) -> str:
    return NO_DATA if value is None else f"{value:.2f}"


def _day(value: date | None) -> str:
    return NO_DATA if value is None else value.isoformat()


def _at(days: Sequence[date], index: int) -> date | None:
    return days[index] if 0 <= index < len(days) else None


def _row(
    one: Series, found: SeriesCloses, zero: DayZero, days: Sequence[date]
) -> tuple[str, bool]:
    """A series' row, and whether it used a day from the backup."""
    if zero.session is None:
        cells = [NO_DATA] * 8
        return _join([one.name, zero.aligned.isoformat(), *cells, NOT_YET]), False
    index = days.index(zero.session)
    before_2, before, after, fifth = (
        _at(days, index + offset) for offset in (-2, -1, 1, 5)
    )
    # The sessions from day −2 to day +5 that the data has.
    window = days[max(index - 2, 0) : index + 6]

    def close(day: date | None) -> float | None:
        return None if day is None else found.closes.get(day)

    notes = [DURING] if zero.during else []
    notes += [f"Yahoo 回應缺 {day} 這一根" for day in window if day not in found.closes]
    notes += [
        f"{day} 的收盤取自 {_backup_name(one)}" for day in window if day in found.filled
    ]
    notes += [
        f"視窗內有除息日 {day}（收盤未調整）"
        for day in sorted(found.dividends)
        if window[0] <= day <= window[-1]
    ]
    cells = [
        one.name,
        zero.aligned.isoformat(),
        _day(before),
        _close(close(before)),
        _percent(close(before_2), close(before)),
        zero.session.isoformat(),
        _close(close(zero.session)),
        _percent(close(before), close(zero.session)),
        _percent(close(zero.session), close(after)),
        _percent(close(before), close(fifth)),
        "；".join(notes),
    ]
    shown = (before_2, before, zero.session, after, fifth)
    return _join(cells), any(day in found.filled for day in shown)


def _backup_name(one: Series) -> str:
    return "" if one.backup is None else BACKUP_NAMES[one.backup.source]


def _join(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _sources(uses_backup: bool) -> str:
    return "、".join(
        [YAHOO_SOURCE_ID, BACKUP_SOURCE_ID] if uses_backup else [YAHOO_SOURCE_ID]
    )


def _first_line(
    event: Event, listed: MarketSeries, zeros: dict[str, DayZero], uses_backup: bool
) -> str:
    start = f"> 由程式依日線收盤價計算（資料來源 {_sources(uses_backup)}；收盤未調整除息），不是新聞來源的話。"
    if event.moment is not None:
        return (
            f"{start}事件時刻：{event.moment.isoformat()}（event_time）；各市場的 D0 是收盤時刻在事件時刻當下"
            "或之後的第一個交易日，事件發生在 D0 這一盤的交易時間內的，註欄寫明。"
        )
    aligned = "，".join(
        f"{market.label}序列對準 event_date{'' if zeros[market.code].aligned == event.event_date else ' 隔天'}"
        for market in listed.markets
    )
    return (
        f"{start}事件市場：{event.market.code}；{aligned}，D0 是對準日當天或之後的第一個交易日。"
        "盤後才公布的事件，當日欄反應不到，請看次一交易日欄。"
    )


def section(event: Event, listed: MarketSeries, closes: Closes) -> Section:
    """The section's lines, from its heading to the table's last row."""
    days = {
        market.code: sessions(market, listed.series, closes)
        for market in listed.markets
    }
    zeros = {
        market.code: (
            by_moment(market, event.moment, days[market.code])
            if event.moment is not None
            else by_date(market, event.market, event.event_date, days[market.code])
        )
        for market in listed.markets
    }
    rows = [
        _row(one, closes[one.symbol], zeros[one.market.code], days[one.market.code])
        for one in listed.series
    ]
    uses_backup = any(used for _, used in rows)
    # By date, an event on a day its market has no session says so, as the earlier files do.
    not_a_session = (
        event.moment is None and event.event_date not in days[event.market.code]
    )
    note = (
        [f"> 行情註：event_date {event.event_date} 不是交易日，D0 取之後第一個交易日。"]
        if not_a_session
        else []
    )
    lines = (
        f"## {HEADING}",
        "",
        _first_line(event, listed, zeros, uses_backup),
        *note,
        "",
        HEADER,
        RULE,
        *(row for row, _ in rows),
    )
    return Section(lines, uses_backup)
