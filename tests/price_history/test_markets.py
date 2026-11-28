"""Day 0 of each market, from the moment of an event or from its date, and the series file."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from chat_bridge.price_history.markets import (
    MarketSeriesFileError,
    by_date,
    by_moment,
    market_series,
)

LISTED = market_series()
TW = LISTED.market("TW")
US = LISTED.market("US")
TAIPEI = ZoneInfo("Asia/Taipei")
NEW_YORK = ZoneInfo("America/New_York")
# 2026-11-20 is a Friday, 2026-11-23 the Monday after it.
SESSIONS = [date(2026, 11, day) for day in (18, 19, 20, 23, 24, 25)]


def test_the_sample_file_lists_the_nine_series_and_two_markets() -> None:
    assert [market.code for market in LISTED.markets] == ["US", "TW"]
    assert len(LISTED.series) == 9
    assert [one.symbol for one in LISTED.series if one.backup] == [
        "^TWII",
        "2330.TW",
        "2308.TW",
        "0050.TW",
        "006208.TW",
    ]


def test_the_series_of_a_market_are_listed_in_order() -> None:
    assert TW is not None
    assert [one.symbol for one in LISTED.of_market(TW)] == [
        "^TWII",
        "2330.TW",
        "2308.TW",
        "0050.TW",
        "006208.TW",
    ]


def test_a_market_day_event_at_the_taiwan_close_is_on_that_session_in_both_markets() -> (
    None
):
    assert TW is not None and US is not None
    moment = datetime(2026, 11, 24, 13, 30, tzinfo=TAIPEI)

    assert by_moment(TW, moment, SESSIONS).session == date(2026, 11, 24)
    assert by_moment(US, moment, SESSIONS).session == date(2026, 11, 24)


def test_results_after_the_us_close_are_on_each_markets_next_session() -> None:
    assert TW is not None and US is not None
    moment = datetime(2026, 11, 19, 16, 5, tzinfo=NEW_YORK)

    assert by_moment(US, moment, SESSIONS).session == date(2026, 11, 20)
    assert by_moment(TW, moment, SESSIONS).session == date(2026, 11, 20)


def test_a_fed_release_during_the_us_session_is_on_that_session_and_says_so() -> None:
    assert TW is not None and US is not None
    moment = datetime(2026, 11, 18, 14, 0, tzinfo=NEW_YORK)

    us = by_moment(US, moment, SESSIONS)
    tw = by_moment(TW, moment, SESSIONS)

    assert (us.session, us.during) == (date(2026, 11, 18), True)
    assert (tw.session, tw.during) == (date(2026, 11, 19), False)


def test_a_moment_on_a_day_without_a_session_is_on_the_next_session() -> None:
    assert TW is not None
    moment = datetime(2026, 11, 21, 10, 0, tzinfo=TAIPEI)

    assert by_moment(TW, moment, SESSIONS).session == date(2026, 11, 23)


def test_a_moment_after_the_data_has_no_session_yet() -> None:
    assert TW is not None
    moment = datetime(2026, 11, 25, 14, 0, tzinfo=TAIPEI)

    assert by_moment(TW, moment, SESSIONS).session is None


@pytest.mark.parametrize(
    ("event_market", "taiwan_day", "us_day"),
    [
        ("US", date(2026, 11, 20), date(2026, 11, 19)),
        ("TW", date(2026, 11, 19), date(2026, 11, 19)),
    ],
)
def test_by_date_taiwan_follows_a_us_event_the_next_day(
    event_market: str, taiwan_day: date, us_day: date
) -> None:
    assert TW is not None and US is not None
    event = LISTED.market(event_market)
    assert event is not None
    event_date = date(2026, 11, 19)

    assert by_date(TW, event, event_date, SESSIONS).aligned == taiwan_day
    assert by_date(US, event, event_date, SESSIONS).aligned == us_day


def test_by_date_day_0_is_the_first_session_on_or_after_the_aligned_day() -> None:
    assert US is not None
    saturday = date(2026, 11, 21)

    zero = by_date(US, US, saturday, SESSIONS)

    assert (zero.aligned, zero.session) == (saturday, date(2026, 11, 23))


def test_a_series_of_an_unlisted_market_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "market_series.json"
    path.write_text(
        json.dumps(
            {
                "about": "x",
                "markets": [
                    {
                        "code": "TW",
                        "label": "台股",
                        "zone": "Asia/Taipei",
                        "opens": "09:00",
                        "closes": "13:30",
                    }
                ],
                "series": [{"symbol": "^GSPC", "name": "S&P 500", "market": "US"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(MarketSeriesFileError, match="no listed market"):
        market_series.__wrapped__(path)


def test_the_us_session_moves_with_daylight_saving() -> None:
    assert US is not None
    summer, winter = US.close_at(date(2026, 7, 1)), US.close_at(date(2026, 12, 1))

    assert summer.utcoffset() == timedelta(hours=-4)
    assert winter.utcoffset() == timedelta(hours=-5)
