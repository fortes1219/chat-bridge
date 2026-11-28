"""The lookups a split names, checked before anything is read."""

from dataclasses import dataclass
from datetime import date

import pytest

from chat_bridge.price_history.lookups import (
    MOST_LOOKUPS,
    LeftOutReason,
    check,
    place,
)
from chat_bridge.price_history.markets import market_series

LISTED = market_series()
TODAY = date(2026, 11, 28)
NAMES = {"2454.TW": "聯發科 / MediaTek"}


@dataclass
class Asked:
    symbol: str
    start_date: str = "2026-09-01"
    end_date: str = "2026-11-27"


def test_a_listed_series_keeps_its_name_and_its_backup() -> None:
    series = place("006208.TW", LISTED, NAMES)

    assert series is not None
    assert series.name == "富邦台50 006208"
    assert series.backup is not None and series.backup.id == "006208"


def test_a_taiwan_listing_is_placed_with_finmind_and_a_holding_by_its_name() -> None:
    held = place("2454.TW", LISTED, NAMES)
    otc = place("6488.TWO", LISTED, NAMES)

    assert held is not None and held.market.code == "TW"
    assert held.name == "聯發科 / MediaTek"
    assert held.backup is not None and held.backup.id == "2454"
    assert otc is not None and otc.backup is not None and otc.backup.id == "6488"


def test_a_us_listing_is_placed_without_a_backup() -> None:
    series = place("NVDA", LISTED, NAMES)

    assert series is not None
    assert (series.market.code, series.name, series.backup) == ("US", "NVDA", None)


def test_the_kept_lookups_keep_their_order_and_their_symbol_is_read_as_written() -> (
    None
):
    checked = check(
        [Asked(" nvda "), Asked("0050.TW", "2026-11-06", "2026-11-06")],
        TODAY,
        LISTED,
        NAMES,
    )

    assert [(k.series.symbol, k.start, k.end) for k in checked.kept] == [
        ("NVDA", date(2026, 9, 1), date(2026, 11, 27)),
        ("0050.TW", date(2026, 11, 6), date(2026, 11, 6)),
    ]
    assert checked.left_out == ()


@pytest.mark.parametrize(
    ("asked", "reason"),
    [
        pytest.param(Asked("CASH"), LeftOutReason.CASH, id="cash"),
        pytest.param(Asked("cash"), LeftOutReason.CASH, id="cash in lower case"),
        pytest.param(Asked("7203.T"), LeftOutReason.UNKNOWN_SYMBOL, id="Tokyo"),
        pytest.param(Asked("BTC-USD"), LeftOutReason.UNKNOWN_SYMBOL, id="a coin"),
        pytest.param(Asked("台積電"), LeftOutReason.UNKNOWN_SYMBOL, id="a name"),
        pytest.param(
            Asked("NVDA", "2026-02-30"), LeftOutReason.NOT_A_DATE, id="no such day"
        ),
        pytest.param(
            Asked("NVDA", "2026/09/01"), LeftOutReason.NOT_A_DATE, id="slashes"
        ),
        pytest.param(
            Asked("NVDA", "20260901"), LeftOutReason.NOT_A_DATE, id="no dashes"
        ),
        pytest.param(
            Asked("NVDA", "2026-11-02", "2026-11-01"),
            LeftOutReason.START_AFTER_END,
            id="backwards",
        ),
        pytest.param(
            Asked("NVDA", "2026-11-01", "2026-11-29"),
            LeftOutReason.IN_THE_FUTURE,
            id="tomorrow",
        ),
        pytest.param(
            Asked("NVDA", "2025-11-27", "2026-11-28"),
            LeftOutReason.TOO_LONG,
            id="a day past a year",
        ),
    ],
)
def test_a_lookup_that_fails_a_check_is_left_out_with_its_reason(
    asked: Asked, reason: LeftOutReason
) -> None:
    checked = check([asked, Asked("NVDA")], TODAY, LISTED, NAMES)

    assert [one.reason for one in checked.left_out] == [reason]
    assert checked.left_out[0].symbol == asked.symbol
    assert [k.series.symbol for k in checked.kept] == ["NVDA"]


def test_a_year_to_the_day_is_kept() -> None:
    checked = check([Asked("NVDA", "2025-11-29", "2026-11-28")], TODAY, LISTED, NAMES)

    assert len(checked.kept) == 1


def test_a_repeated_lookup_is_kept_once() -> None:
    checked = check([Asked("NVDA"), Asked("nvda")], TODAY, LISTED, NAMES)

    assert len(checked.kept) == 1
    assert [one.reason for one in checked.left_out] == [LeftOutReason.REPEATED]


def test_lookups_past_the_most_are_left_out() -> None:
    asked = [
        Asked("NVDA", f"2026-{month:02d}-01", "2026-11-27") for month in range(1, 12)
    ]
    asked += [Asked(symbol) for symbol in ("AAPL", "MSFT", "AMZN", "META", "GOOG")]
    asked += [Asked(f"{code}.TW") for code in range(2300, 2330)]

    checked = check(asked, TODAY, LISTED, NAMES)

    assert len(checked.kept) == MOST_LOOKUPS
    assert {one.reason for one in checked.left_out} == {LeftOutReason.TOO_MANY}
    assert len(checked.left_out) == len(asked) - MOST_LOOKUPS
