"""What the lookups give and the `<prices>` block: the trend, the days of a short period, each
event's rows, the shared rows and the bound."""

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from chat_bridge.price_history import block
from chat_bridge.price_history.block import FoundEvent, prices, trend
from chat_bridge.price_history.closes import ClosesError, SeriesCloses
from chat_bridge.price_history.lookups import LeftOut, LeftOutReason, Lookup, place
from chat_bridge.price_history.markets import market_series
from chat_bridge.price_history.reading import Reads, SymbolRead
from chat_bridge.price_history.schemas import NotRead

LISTED = market_series()
READ_AT = datetime(2026, 11, 28, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))
# Thursday 2026-11-05 to Friday 2026-11-13: seven sessions.
SESSIONS = [date(2026, 11, day) for day in (5, 6, 9, 10, 11, 12, 13)]
CLOSES_0050 = dict(
    zip(SESSIONS, [100.0, 95.0, 97.0, 90.0, 96.0, 99.0, 98.0], strict=True)
)


def _lookup(symbol: str, start: date = SESSIONS[0], end: date = SESSIONS[-1]) -> Lookup:
    series = place(symbol, LISTED, {})
    assert series is not None
    return Lookup(series, start, end)


def _reads(
    closes: dict[str, dict[date, float]], failed: dict[str, str] | None = None
) -> Reads:
    by_symbol = {}
    for symbol, found in closes.items():
        series = place(symbol, LISTED, {})
        assert series is not None
        by_symbol[symbol] = SymbolRead(
            series, SeriesCloses(dict(found)), None, False, READ_AT
        )
    for symbol, error in (failed or {}).items():
        series = place(symbol, LISTED, {})
        assert series is not None
        by_symbol[symbol] = SymbolRead(series, None, ClosesError(error), False, None)
    return Reads(by_symbol, {"TW": SESSIONS, "US": SESSIONS})


def _event(
    file: str,
    day: date,
    markets: tuple[str, ...] = ("TW",),
    numbers: tuple[int, ...] = (1,),
) -> FoundEvent:
    return FoundEvent(file, day, markets, None, numbers)


def test_the_trend_is_the_change_the_extremes_and_the_largest_fall_from_a_high() -> (
    None
):
    found = trend(CLOSES_0050, SESSIONS)

    assert found is not None
    assert (found.first_day, found.first_close) == (date(2026, 11, 5), 100.0)
    assert (found.last_day, found.last_close) == (date(2026, 11, 13), 98.0)
    assert found.change == -2.0
    assert (found.high_day, found.high) == (date(2026, 11, 5), 100.0)
    assert (found.low_day, found.low) == (date(2026, 11, 10), 90.0)
    assert found.largest_fall == -10.0
    assert (found.fall_from, found.fall_to) == (date(2026, 11, 5), date(2026, 11, 10))


def test_a_period_that_only_rises_has_no_fall() -> None:
    found = trend({SESSIONS[0]: 10.0, SESSIONS[1]: 11.0}, SESSIONS[:2])

    assert found is not None
    assert (found.largest_fall, found.fall_from, found.fall_to) == (0.0, None, None)


def test_a_period_without_a_trading_day_has_no_trend() -> None:
    assert trend(CLOSES_0050, []) is None


def test_a_short_period_has_every_trading_day_with_its_change() -> None:
    given = prices(
        [_lookup("0050.TW", SESSIONS[1], SESSIONS[2])],
        [],
        _reads({"0050.TW": CLOSES_0050}),
        [],
        LISTED,
    )

    [view] = given.view.lookups
    assert [(d.day, d.close, d.change) for d in view.days] == [
        (date(2026, 11, 6), 95.0, -5.0),
        (date(2026, 11, 9), 97.0, 2.11),
    ]
    assert "| 0050.TW | 2026-11-06 | 95.00 | -5.00% |" in given.block


def test_a_long_period_has_no_rows_of_its_days() -> None:
    sessions = [SESSIONS[0] + timedelta(days=n) for n in range(11)]
    closes = {day: 100.0 + n for n, day in enumerate(sessions)}
    reads = Reads(_reads({"0050.TW": closes}).by_symbol, {"TW": sessions})

    given = prices(
        [_lookup("0050.TW", sessions[0], sessions[-1])], [], reads, [], LISTED
    )

    assert given.view.lookups[0].days == []
    assert "Every trading day" not in given.block


def test_an_event_has_the_market_sections_values_on_its_day_and_after() -> None:
    given = prices(
        [_lookup("0050.TW")],
        [],
        _reads({"0050.TW": CLOSES_0050}),
        [_event("2026-11-06-a.md", date(2026, 11, 6), numbers=(3, 7))],
        LISTED,
    )

    [event] = given.view.events
    [row] = event.rows
    assert (row.d0, row.close, row.day_change, row.next_change) == (
        date(2026, 11, 6),
        95.0,
        -5.0,
        2.11,
    )
    # D+5 is 2026-11-13, against the trading day before D0.
    assert row.fifth_change == -2.0
    assert "2026-11-06-a.md, event date 2026-11-06, sources [3] [7]:" in given.block
    assert (
        "| 0050.TW | 2026-11-06 | 95.00 | -5.00% | +2.11% | -2.00% |  |" in given.block
    )


def test_a_us_event_reaches_taiwan_the_next_session() -> None:
    given = prices(
        [_lookup("0050.TW")],
        [],
        _reads({"0050.TW": CLOSES_0050}),
        [_event("us.md", date(2026, 11, 6), ("US",))],
        LISTED,
    )

    [row] = given.view.events[0].rows
    assert (row.aligned, row.d0) == (date(2026, 11, 7), date(2026, 11, 9))


def test_an_event_outside_every_period_or_without_a_market_has_no_rows() -> None:
    given = prices(
        [_lookup("0050.TW", SESSIONS[0], SESSIONS[2])],
        [],
        _reads({"0050.TW": CLOSES_0050}),
        [
            _event("later.md", date(2026, 11, 12)),
            _event("own.md", date(2026, 11, 6), ()),
        ],
        LISTED,
    )

    assert given.view.events == []
    assert "Events of the sources" not in given.block


def test_an_event_whose_rows_equal_an_earlier_ones_names_its_file() -> None:
    given = prices(
        [_lookup("0050.TW")],
        [],
        _reads({"0050.TW": CLOSES_0050}),
        [
            _event("first.md", date(2026, 11, 6), numbers=(1,)),
            _event("second.md", date(2026, 11, 6), numbers=(4,)),
            _event("third.md", date(2026, 11, 9), numbers=(5,)),
        ],
        LISTED,
    )

    events = given.view.events
    assert [(e.file, e.same_as, len(e.rows)) for e in events] == [
        ("first.md", None, 1),
        ("second.md", "first.md", 0),
        ("third.md", None, 1),
    ]
    assert (
        "second.md, event date 2026-11-06, sources [4]: same rows as first.md"
        in given.block
    )


def test_the_only_numbers_in_brackets_are_the_sources_numbers() -> None:
    given = prices(
        [_lookup("0050.TW"), _lookup("2330.TW")],
        [],
        _reads({"0050.TW": CLOSES_0050, "2330.TW": CLOSES_0050}),
        [
            _event(f"{n}.md", day, numbers=(n, n + 20))
            for n, day in enumerate(SESSIONS[:4], 2)
        ],
        LISTED,
    )

    bracketed = {int(n) for n in re.findall(r"\[(\d+)\]", given.block)}
    assert bracketed == {2, 3, 4, 5, 22, 23, 24, 25}


def test_past_the_bound_every_trend_is_kept_and_the_later_events_are_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(block, "BLOCK_BOUND", 2_500)
    many = [
        _event(f"event-{n:02d}.md", SESSIONS[n % 4], numbers=(n,)) for n in range(1, 30)
    ]
    lookups = [_lookup("0050.TW"), _lookup("2330.TW")]
    closes = {
        "0050.TW": CLOSES_0050,
        "2330.TW": {d: c * 2 for d, c in CLOSES_0050.items()},
    }

    given = prices(lookups, [], _reads(closes), many, LISTED)

    assert len(given.block) <= 2_500
    assert len(given.view.lookups) == 2
    kept = given.view.events
    assert kept and [e.file for e in kept] == [e.file for e in many[: len(kept)]]
    assert given.view.events_left_out == len(many) - len(kept)
    assert (
        f"{given.view.events_left_out} more events' rows were left out" in given.block
    )


def test_a_symbol_that_was_not_read_says_why_and_has_no_rows() -> None:
    given = prices(
        [_lookup("NVDA"), _lookup("0050.TW")],
        [],
        _reads({"0050.TW": CLOSES_0050}, {"NVDA": "Yahoo NVDA: timed out"}),
        [_event("a.md", date(2026, 11, 6), ("US",))],
        LISTED,
    )

    nvda = given.view.lookups[0]
    assert nvda.trend is None
    assert nvda.not_read == NotRead(source="yahoo", reason="unreadable")
    assert (
        "- NVDA, 2026-11-05 to 2026-11-13: not read: Yahoo Finance could not be read"
        in given.block
    )
    # The source's own message goes to the record only.
    assert "timed out" not in given.block
    assert given.errors == {"NVDA": "Yahoo NVDA: timed out"}
    assert [row.symbol for row in given.view.events[0].rows] == ["0050.TW"]


@pytest.mark.parametrize(
    ("error", "said"),
    [
        (
            ClosesError("Yahoo X: no daily data", reason="no_data"),
            "Yahoo Finance had no daily closes for it",
        ),
        (ClosesError("FinMind: 402", source="finmind"), "FinMind could not be read"),
    ],
)
def test_each_reason_and_source_is_said_in_a_fixed_sentence(
    error: ClosesError, said: str
) -> None:
    reads = _reads({"0050.TW": CLOSES_0050})
    series = place("NVDA", LISTED, {})
    assert series is not None
    reads.by_symbol["NVDA"] = SymbolRead(series, None, error, False, None)

    given = prices([_lookup("NVDA")], [], reads, [], LISTED)

    assert f"not read: {said}" in given.block


def test_a_largest_fall_has_no_plus_sign() -> None:
    rising = {SESSIONS[0]: 10.0, SESSIONS[1]: 11.0}
    reads = Reads(_reads({"0050.TW": rising}).by_symbol, {"TW": SESSIONS[:2]})

    given = prices(
        [_lookup("0050.TW", SESSIONS[0], SESSIONS[1])], [], reads, [], LISTED
    )

    assert "largest fall from a high 0.00%" in given.block
    assert "+0.00%" not in given.block.split("largest fall")[1].split("\n")[0]


def test_the_whole_block_stays_within_the_bound_and_every_lookup_line_is_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(block, "BLOCK_BOUND", 1_900)
    symbols = ("0050.TW", "2330.TW", "2308.TW", "006208.TW")
    lookups = [_lookup(symbol) for symbol in symbols]
    closes = dict.fromkeys(symbols, CLOSES_0050)
    many = [_event(f"e{n}.md", SESSIONS[n % 4], numbers=(n,)) for n in range(1, 10)]

    given = prices(lookups, [], _reads(closes), many, LISTED)

    assert len(given.block) <= 1_900
    assert given.block.count("\n- ") == 4
    kept_days = [one for one in given.view.lookups if one.days]
    assert given.view.days_left_out == sum(7 for _ in range(4 - len(kept_days)))
    assert given.view.days_left_out > 0
    assert f"{given.view.days_left_out} trading days' rows were left out" in given.block
    assert given.view.events_left_out == len(many) - len(given.view.events)


def test_lookups_left_out_are_named_but_repeats_are_not() -> None:
    left_out = [
        LeftOut("7203.T", "2026-11-01", "2026-11-13", LeftOutReason.UNKNOWN_SYMBOL),
        LeftOut("0050.TW", "2026-11-05", "2026-11-13", LeftOutReason.REPEATED),
    ]

    given = prices(
        [_lookup("0050.TW")], left_out, _reads({"0050.TW": CLOSES_0050}), [], LISTED
    )

    assert (
        "Not looked up: 7203.T 2026-11-01 to 2026-11-13 (a symbol of no market the app reads)."
        in given.block
    )
    assert given.block.count("0050.TW 2026-11-05") == 0


def test_hundreds_of_lookups_left_out_are_named_ten_and_counted() -> None:
    left_out = [
        LeftOut(f"X{n}.T", "2026-11-01", "2026-11-13", LeftOutReason.UNKNOWN_SYMBOL)
        for n in range(400)
    ]

    given = prices(
        [_lookup("0050.TW")], left_out, _reads({"0050.TW": CLOSES_0050}), [], LISTED
    )

    [line] = [
        line for line in given.block.splitlines() if line.startswith("Not looked up")
    ]
    assert line.count("(a symbol of no market the app reads)") == block.NAMED_LEFT_OUT
    assert line.endswith("; and 390 more.")


def test_the_block_of_a_failed_split_says_nothing_was_looked_up() -> None:
    assert block.split_failed() == (
        "<prices>\nNo prices were looked up for this question: the split did not finish.\n"
        "</prices>"
    )
