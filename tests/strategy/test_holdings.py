"""The person's own holdings: what the service keeps of what the page sends, the endpoint, and
what the split is given of them.

The store is stubbed, so no database is read; the writes are tested in test_store.py.
"""

import json
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat.server import create_app
from chat_bridge.chat.service import holding_lines
from chat_bridge.chat.split import split_input
from chat_bridge.strategy import store
from chat_bridge.strategy.prices import PriceBook
from chat_bridge.strategy.revision import strategy_input
from chat_bridge.strategy.schemas import (
    HoldingInput,
    HoldingsRequest,
    HoldingView,
    RuleChecks,
    StoredStrategy,
)
from chat_bridge.strategy.state import STATE

HOLDINGS = "/strategy/holdings"
STORED = StoredStrategy(
    holdings=[],
    targets=[],
    targets_total=100,
    rule_checks=RuleChecks(met=0, enabled=0, rules=[]),
    proposal=None,
    notice=store.SAMPLE_NOTICE,
)


def _holding(symbol: str, **changes: Any) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "names": {"zh-TW": "名稱", "en": "Name"},
        "quantity": "10",
        "average_cost": "100.5",
    } | changes


def _check(*holdings: dict[str, Any], cash: str = "1000") -> list[HoldingView]:
    request = HoldingsRequest(
        holdings=[HoldingInput.model_validate(holding) for holding in holdings],
        cash=Decimal(cash),
    )
    return store.check_holdings(request)


def _refused(*holdings: dict[str, Any], cash: str = "1000") -> tuple[str, str]:
    with pytest.raises(store.HoldingRefusedError) as refused:
        _check(*holdings, cash=cash)
    return refused.value.code, str(refused.value)


@pytest.mark.parametrize(
    ("symbol", "market", "currency"),
    [
        ("2330.TW", "TW", "TWD"),
        ("006208.TW", "TW", "TWD"),
        ("00631L.TW", "TW", "TWD"),
        ("6488.TWO", "TW", "TWD"),
        ("AAPL", "US", "USD"),
        ("BRK-B", "US", "USD"),
        (" nvda ", "US", "USD"),
    ],
)
def test_a_taiwan_or_us_listing_is_kept_with_the_market_and_currency_of_its_symbol(
    symbol: str, market: str, currency: str
) -> None:
    [kept] = _check(_holding(symbol))

    assert kept.symbol == symbol.strip().upper()
    assert (kept.market, kept.currency) == (market, currency)
    assert kept.quantity == Decimal("10")
    assert kept.average_cost == Decimal("100.5")


@pytest.mark.parametrize(
    "symbol",
    # Another market's suffix, an index, a currency pair, a coin, the cash's own symbol, nothing.
    ["0700.HK", "7203.T", "VOD.L", "^GSPC", "^SOX", "USDTWD=X", "BTC-USD", "CASH", ""],
)
def test_a_symbol_of_no_taiwan_or_us_listing_is_refused(symbol: str) -> None:
    code, message = _refused(_holding("AAPL"), _holding(symbol))

    assert code == "holding_symbol"
    assert message.startswith("holding 2:")


@pytest.mark.parametrize(
    ("holding", "code"),
    [
        (_holding("AAPL", names={"zh-TW": "蘋果", "en": " "}), "holding_name"),
        (_holding("AAPL", names={"zh-TW": "蘋果"}), "holding_name"),
        (_holding("AAPL", names={"zh-TW": "長" * 41, "en": "Apple"}), "holding_name"),
        (_holding("AAPL", quantity="0"), "holding_amount"),
        (_holding("AAPL", quantity="-1"), "holding_amount"),
        (_holding("AAPL", quantity="1e16"), "holding_amount"),
        (_holding("AAPL", average_cost="-0.01"), "holding_amount"),
    ],
)
def test_a_holding_without_a_name_or_with_an_amount_out_of_range_is_refused(
    holding: dict[str, Any], code: str
) -> None:
    assert _refused(holding)[0] == code


def test_a_symbol_listed_twice_is_refused_however_it_is_written() -> None:
    assert _refused(_holding("NVDA"), _holding("nvda "))[0] == "holding_repeated"


def test_cash_below_zero_is_refused_and_zero_cash_is_kept() -> None:
    assert _refused(cash="-1")[0] == "holding_amount"
    assert _check(cash="0") == []


def test_more_holdings_than_the_limit_are_refused() -> None:
    many = [
        _holding(f"{2000 + number}.TW") for number in range(store.MOST_HOLDINGS + 1)
    ]

    assert _refused(*many)[0] == "holdings_too_many"


@pytest.fixture
def saved(monkeypatch: pytest.MonkeyPatch) -> list[list[HoldingView]]:
    """Each list of holdings the endpoint saved, checked as the store checks them, and the
    holdings the prices were then made to follow."""
    kept: list[list[HoldingView]] = []

    async def save(request: HoldingsRequest) -> StoredStrategy:
        kept.append(store.check_holdings(request))
        return STORED

    async def read() -> StoredStrategy:
        return STORED

    def follow(holdings: list[HoldingView]) -> None:
        kept.append(holdings)

    monkeypatch.setattr(store, "save_holdings", save)
    monkeypatch.setattr(store, "read_strategy", read)
    monkeypatch.setattr(STATE, "follow", follow)
    return kept


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def test_json_holdings_are_saved_and_the_prices_follow_them(
    client: TestClient, saved: list[list[HoldingView]]
) -> None:
    response = client.put(
        HOLDINGS, json={"holdings": [_holding("AAPL")], "cash": "500"}
    )

    assert response.status_code == 200
    [checked, followed] = saved
    assert [holding.symbol for holding in checked] == ["AAPL"]
    assert followed == STORED.holdings


def test_a_holding_the_service_cannot_keep_is_refused_with_its_code_and_place(
    client: TestClient, saved: list[list[HoldingView]]
) -> None:
    response = client.put(
        HOLDINGS,
        json={"holdings": [_holding("AAPL"), _holding("0700.HK")], "cash": "500"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert (detail["code"], detail["item"]) == ("holding_symbol", 2)
    assert detail["message"].startswith("holding 2:")
    assert saved == []


def test_a_refusal_about_the_whole_request_names_no_holding(
    client: TestClient, saved: list[list[HoldingView]]
) -> None:
    response = client.put(HOLDINGS, json={"holdings": [], "cash": "-1"})

    assert response.json()["detail"]["code"] == "holding_amount"
    assert response.json()["detail"]["item"] is None


@pytest.mark.parametrize(
    "send",
    [
        {"json": {"holdings": [_holding("AAPL") | {"market": "US"}], "cash": "1"}},
        {"json": {"holdings": [], "cash": "1", "targets": {}}},
        {"json": {"holdings": []}},
        {
            "content": '{"holdings": [], "cash": "1"}',
            "headers": {"Content-Type": "text/plain"},
        },
    ],
)
def test_another_field_a_missing_cash_or_a_post_another_page_can_send_is_refused(
    client: TestClient, saved: list[list[HoldingView]], send: dict[str, Any]
) -> None:
    response = client.put(HOLDINGS, **send)

    assert response.status_code == 422
    assert saved == []


def test_the_split_is_given_each_holding_but_cash_by_its_symbol_and_names() -> None:
    held = _check(
        _holding("2330.TW", names={"zh-TW": "台積電", "en": "TSMC"}),
        _holding("AAPL", names={"zh-TW": "Apple", "en": "Apple"}),
    )
    cash = held[0].model_copy(update={"symbol": "CASH", "market": None})
    profile = store.Profile(holdings=[*held, cash], targets={}, rules=[])

    lines = holding_lines(profile)

    assert lines == ["2330.TW: 台積電 / TSMC", "AAPL: Apple"]
    sent = split_input("依最近的事件調整我的策略", lines)
    assert sent.index("<holdings>\n2330.TW") < sent.index("<question>")
    assert holding_lines(None) == []
    assert "<holdings>" not in split_input("聯準會升息", [])


def test_the_model_reads_amounts_in_plain_notation_and_no_value_without_a_price() -> (
    None
):
    # The database may hand 20000 back as 2E+4.
    [held] = _check(_holding("0050.TW"))
    held = held.model_copy(update={"quantity": Decimal("2E+4")})
    profile = store.Profile(holdings=[held], targets={"0050.TW": 100}, rules=[])

    data = json.loads(
        strategy_input(profile, PriceBook())
        .removeprefix("<strategy>\n")
        .removesuffix("</strategy>\n")
    )

    [row] = data["holdings"]
    assert row["quantity"] == "20000"
    assert (row["value_TWD"], row["weight_percent"], row["latest_price"]) == (
        None,
        None,
        None,
    )
    assert data["left_out"] == ["0050.TW"]
    assert data["targets_total_percent"] == 100
