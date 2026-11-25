"""The previous close of a day, from what the sources gave of a series' recent days (spec 012)."""

from datetime import UTC, date, datetime
from decimal import Decimal

from chat_bridge.strategy.history import History, change_day

D = Decimal
# 2026-11-21 and 22 are a weekend.
CLOSES = {
    date(2026, 11, 19): D("90.20"),
    date(2026, 11, 20): D("84.45"),
    date(2026, 11, 23): D("87.00"),
    date(2026, 11, 24): D("95.70"),
}
READ_ON = date(2026, 11, 25)


def test_the_previous_close_is_the_close_of_the_trading_day_before() -> None:
    history = History(read_on=READ_ON, closes=CLOSES)

    assert history.previous_close(date(2026, 11, 25)) == D("95.70")
    # Across a weekend: Friday's close.
    assert history.previous_close(date(2026, 11, 23)) == D("84.45")


def test_a_day_listed_without_a_close_is_never_filled_by_an_earlier_one() -> None:
    history = History(
        read_on=READ_ON, closes=CLOSES, missing=frozenset({date(2026, 11, 24)})
    )
    closes = {day: close for day, close in CLOSES.items() if day != date(2026, 11, 24)}

    assert (
        History(
            read_on=READ_ON, closes=closes, missing=frozenset({date(2026, 11, 24)})
        ).previous_close(date(2026, 11, 25))
        is None
    )
    # A source that has the day fills it.
    assert history.merged(History(read_on=READ_ON, closes=CLOSES)).previous_close(
        date(2026, 11, 25)
    ) == D("95.70")


def test_the_day_read_on_gives_no_later_day_its_previous_close() -> None:
    # Read on 11-24 while it traded: its value then is not its close.
    history = History(read_on=date(2026, 11, 24), closes=CLOSES)

    assert history.previous_close(date(2026, 11, 24)) == D("87.00")
    assert history.previous_close(date(2026, 11, 25)) is None


def test_a_day_after_the_day_read_on_gets_no_older_close() -> None:
    # Read on 11-24 before it opened: the sources had up to 11-23, and 11-24's close is unknown.
    closes = {day: close for day, close in CLOSES.items() if day < date(2026, 11, 24)}
    history = History(read_on=date(2026, 11, 24), closes=closes)

    assert history.previous_close(date(2026, 11, 25)) is None


def test_a_value_read_while_its_day_traded_is_no_close_once_a_later_read_is_in() -> (
    None
):
    read_while_trading = History(
        read_on=date(2026, 11, 24),
        closes={**CLOSES, date(2026, 11, 24): D("93.10")},
    )
    # The later read lists 11-24 without a close.
    later = History(
        read_on=READ_ON,
        closes={date(2026, 11, 23): D("87.00")},
        missing=frozenset({date(2026, 11, 24)}),
    )

    assert read_while_trading.merged(later).previous_close(READ_ON) is None
    assert read_while_trading.merged(
        History(read_on=READ_ON, closes={date(2026, 11, 24): D("95.70")})
    ).previous_close(READ_ON) == D("95.70")


def test_an_ex_dividend_day_is_measured_from_the_exchanges_reference_price() -> None:
    # 0050 on 2026-07-21: closed 99.20 the day before, reference price 98.60.
    history = History(
        read_on=date(2026, 7, 22),
        closes={date(2026, 7, 20): D("99.20"), date(2026, 7, 21): D("102.50")},
        given={date(2026, 7, 21): D("98.60")},
    )

    assert history.previous_close(date(2026, 7, 21)) == D("98.60")


def test_an_announced_cash_dividend_gives_the_reference_price_until_the_exchanges_arrives() -> (
    None
):
    announced = History(
        read_on=date(2026, 7, 21),
        closes={date(2026, 7, 20): D("99.20")},
        dividends={date(2026, 7, 21): D("0.60")},
    )

    assert announced.previous_close(date(2026, 7, 21)) == D("98.60")
    published = announced.merged(
        History(read_on=date(2026, 7, 21), given={date(2026, 7, 21): D("98.59")})
    )
    assert published.previous_close(date(2026, 7, 21)) == D("98.59")


def test_an_ex_rights_day_or_an_unannounced_amount_gives_no_previous_close() -> None:
    history = History(
        read_on=date(2026, 7, 21),
        closes={date(2026, 7, 20): D("99.20")},
        dividends={date(2026, 7, 21): None},
    )

    assert history.previous_close(date(2026, 7, 21)) is None


def test_the_otc_markets_next_reference_price_is_the_next_days_previous_close() -> None:
    history = History(
        read_on=READ_ON,
        closes={date(2026, 11, 24): D("506.00")},
        next_reference=(date(2026, 11, 24), D("501.50")),
    )

    assert history.previous_close(date(2026, 11, 25)) == D("501.50")


def test_the_next_reference_price_is_for_the_next_day_only() -> None:
    # The OTC table of 11-23, read on 11-24: its reference price is 11-24's.
    history = History(
        read_on=date(2026, 11, 24),
        next_reference=(date(2026, 11, 23), D("501.50")),
    )

    assert history.previous_close(date(2026, 11, 24)) == D("501.50")
    assert history.previous_close(date(2026, 11, 25)) is None


def test_a_us_price_from_the_session_end_on_is_measured_for_the_next_day() -> None:
    # 2026-11-24 in New York: 15:59 in the session, 16:00 its end, 20:30 in the evening.
    assert change_day("NVDA", datetime(2026, 11, 24, 20, 59, tzinfo=UTC)) == date(
        2026, 11, 24
    )
    assert change_day("NVDA", datetime(2026, 11, 24, 21, 0, tzinfo=UTC)) == date(
        2026, 11, 25
    )
    assert change_day("NVDA", datetime(2026, 11, 25, 1, 30, tzinfo=UTC)) == date(
        2026, 11, 25
    )
    # A currency pair's day is the day in London, round the clock.
    assert change_day("TWD=X", datetime(2026, 11, 25, 23, 0, tzinfo=UTC)) == date(
        2026, 11, 25
    )
    # A Taiwan price after its close keeps its day.
    assert change_day("0050.TW", datetime(2026, 11, 25, 8, 0, tzinfo=UTC)) == date(
        2026, 11, 25
    )


def test_a_day_without_any_close_before_it_has_no_previous_close() -> None:
    assert History(read_on=READ_ON).previous_close(READ_ON) is None
    assert (
        History(read_on=READ_ON, closes=CLOSES).previous_close(date(2026, 11, 19))
        is None
    )
