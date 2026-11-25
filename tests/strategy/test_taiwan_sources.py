"""Reading FinMind and the exchanges' open data, with the network replaced by the answers each
source gave on 2026-11-25 (spec 012)."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from chat_bridge.strategy import taiwan_sources
from chat_bridge.strategy.taiwan_sources import (
    SourceError,
    code_of,
    daily_tables,
    finmind_history,
    notices,
)

D = Decimal
TODAY = date(2026, 11, 25)
FINMIND_PRICES = {
    "0050": [
        {"date": "2026-11-23", "stock_id": "0050", "close": 87.0, "spread": 2.55},
        {"date": "2026-11-24", "stock_id": "0050", "close": 95.7, "spread": 8.7},
        {"date": "2026-11-25", "stock_id": "0050", "close": 90.3, "spread": -5.4},
    ],
    "6488": [
        {"date": "2026-11-24", "stock_id": "6488", "close": 506.0, "spread": 45.5}
    ],
}
FINMIND_RESULTS = {
    "0050": [
        {
            "date": "2026-07-21",
            "stock_id": "0050",
            "before_price": 99.2,
            "reference_price": 98.6,
        }
    ],
}
LISTED_DAILY = [
    {"Date": "1151124", "Code": "0050", "ClosingPrice": "95.70", "Change": "8.7000"},
    {
        "Date": "1151124",
        "Code": "2330",
        "ClosingPrice": "2230.00",
        "Change": "200.0000",
    },
    {"Date": "1151124", "Code": "0056", "ClosingPrice": "40.00", "Change": "X0.00"},
]
OTC_DAILY = [
    {
        "Date": "1151124",
        "SecuritiesCompanyCode": "6488",
        "Close": "506.00",
        "Change": "+45.50",
        "NextReferencePrice": "506.00",
    }
]
LISTED_NOTICES = [
    {"Date": "1151202", "Code": "0050", "Exdividend": "息", "CashDividend": "0.75"},
    {"Date": "1151203", "Code": "2330", "Exdividend": "權息", "CashDividend": "6.0"},
    {"Date": "1151120", "Code": "2308", "Exdividend": "息", "CashDividend": "5.0"},
    {"Date": "1151204", "Code": "0056", "Exdividend": "息", "CashDividend": ""},
]
OTC_NOTICES = [
    {
        "ExRrightsExDividendDate": "1151126",
        "SecuritiesCompanyCode": "6488",
        "ExRrightsExDividend": "除息",
        "CashDividend": "4.50000000",
    }
]


@pytest.fixture
def requests_made(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    made: list[str] = []

    def answer(url: str, params: dict[str, str] | None = None) -> Any:
        made.append(
            url if params is None else f"{params['dataset']}:{params['data_id']}"
        )
        if url == taiwan_sources.FINMIND_URL:
            assert params is not None
            table = (
                FINMIND_PRICES
                if params["dataset"] == "TaiwanStockPrice"
                else FINMIND_RESULTS
            )
            return {
                "msg": "success",
                "status": 200,
                "data": table.get(params["data_id"], []),
            }
        return {
            taiwan_sources.LISTED_DAILY_URL: LISTED_DAILY,
            taiwan_sources.OTC_DAILY_URL: OTC_DAILY,
            taiwan_sources.LISTED_NOTICES_URL: LISTED_NOTICES,
            taiwan_sources.OTC_NOTICES_URL: OTC_NOTICES,
        }[url]

    monkeypatch.setattr(taiwan_sources, "_get", answer)
    return made


def test_an_otc_symbol_is_read_by_its_code() -> None:
    assert code_of("6488.TWO") == "6488"
    assert code_of("2330.TW") == "2330"


def test_finmind_gives_the_closes_yahoo_lacked_and_the_reference_prices(
    requests_made: list[str],
) -> None:
    history = finmind_history("0050.TW", TODAY)

    assert history.closes[date(2026, 11, 24)] == D("95.7")
    assert history.given == {date(2026, 7, 21): D("98.6")}
    assert history.previous_close(TODAY) == D("95.7")
    # Two requests a series, by its code.
    assert requests_made == ["TaiwanStockPrice:0050", "TaiwanStockDividendResult:0050"]


def test_a_code_finmind_does_not_know_gives_an_empty_history(
    requests_made: list[str],
) -> None:
    assert finmind_history("9999.TW", TODAY).closes == {}


def test_a_refusal_from_finmind_is_a_source_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(url: str, params: dict[str, str] | None = None) -> Any:
        return {"msg": "Requests reach the upper limit.", "status": 402}

    monkeypatch.setattr(taiwan_sources, "_get", refuse)

    with pytest.raises(SourceError, match="upper limit"):
        finmind_history("0050.TW", TODAY)


def test_rows_in_another_shape_are_left_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer(url: str, params: dict[str, str] | None = None) -> Any:
        if url == taiwan_sources.FINMIND_URL:
            rows: list[Any] = [
                {"close": 95.7},
                {"date": "2026-11-2x", "close": 95.7},
                "not a row",
                {"date": "2026-11-24", "close": 95.7},
            ]
            return {"msg": "success", "status": 200, "data": rows}
        return ["not a row", None, {"Code": "0050"}]

    monkeypatch.setattr(taiwan_sources, "_get", answer)

    assert finmind_history("0050.TW", TODAY).closes == {date(2026, 11, 24): D("95.7")}
    assert notices(["0050.TW", "6488.TWO"], TODAY) == {}
    assert daily_tables(["0050.TW", "6488.TWO"], TODAY, {}) == {}


def test_the_notices_give_the_cash_dividend_alone_and_nothing_for_other_kinds(
    requests_made: list[str],
) -> None:
    found = notices(["0050.TW", "2330.TW", "2308.TW", "0056.TW"], TODAY)

    assert found == {
        "0050.TW": {date(2026, 12, 2): D("0.75")},
        # Rights and dividend together: the notice cannot give the reference price.
        "2330.TW": {date(2026, 12, 3): None},
        # No amount yet.
        "0056.TW": {date(2026, 12, 4): None},
    }
    # 2308's day has passed; and the OTC notice is not read without an OTC holding.
    assert requests_made == [taiwan_sources.LISTED_NOTICES_URL]


def test_the_otc_notice_is_read_for_an_otc_holding(requests_made: list[str]) -> None:
    assert notices(["6488.TWO"], TODAY) == {"6488.TWO": {date(2026, 11, 26): D("4.5")}}
    assert requests_made == [taiwan_sources.OTC_NOTICES_URL]


def test_the_daily_tables_give_the_close_the_changes_previous_close_and_next_reference(
    requests_made: list[str],
) -> None:
    tables = daily_tables(["0050.TW", "6488.TWO", "0056.TW"], TODAY, {})

    listed = tables["0050.TW"]
    # The table's day is before today: its close is today's previous close.
    assert listed.previous_close(TODAY) == D("95.70")
    # Its own day's previous close: the close less the change.
    assert listed.given == {date(2026, 11, 24): D("87.0000")}
    # An ex-dividend day's change is 'X0.00': no previous close from it.
    assert tables["0056.TW"].given == {}
    assert tables["6488.TWO"].next_reference == (date(2026, 11, 24), D("506.00"))
    assert requests_made == [
        taiwan_sources.LISTED_DAILY_URL,
        taiwan_sources.OTC_DAILY_URL,
    ]


def test_a_tables_change_on_an_announced_ex_dividend_day_is_not_used(
    requests_made: list[str],
) -> None:
    tables = daily_tables(
        ["0050.TW"], TODAY, {"0050.TW": {date(2026, 11, 24): D("0.75")}}
    )

    assert tables["0050.TW"].given == {}
