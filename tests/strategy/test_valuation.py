"""The numbers that follow the prices, from fixed holdings and fixed prices."""

from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from chat_bridge.strategy.compute import priced_symbols, valuation
from chat_bridge.strategy.prices import PriceBook, Quote
from chat_bridge.strategy.schemas import HoldingView, Market, PriceTime

NOW = datetime(2026, 11, 24, 1, 30, tzinfo=UTC)
# The US trading day before, as New York names it.
US_DAY = datetime(2026, 11, 21, tzinfo=ZoneInfo("America/New_York"))


def _holding(
    symbol: str, market: Market | None, currency: str, quantity: str, cost: str
) -> HoldingView:
    return HoldingView(
        symbol=symbol,
        names={"zh-TW": symbol, "en": symbol},
        market=market,
        currency=currency,
        quantity=Decimal(quantity),
        average_cost=Decimal(cost),
    )


HOLDINGS = [
    _holding("2330.TW", "TW", "TWD", "2000", "1980"),
    _holding("NVDA", "US", "USD", "150", "142.3"),
    _holding("CASH", None, "TWD", "600000", "1"),
]


def _book(*leave_out: str, **without_previous: bool) -> PriceBook:
    quotes = [
        Quote("2330.TW", Decimal("1480"), Decimal("1495"), "live", NOW),
        Quote("NVDA", Decimal("180"), Decimal("175"), "daily", US_DAY),
        Quote("TWD=X", Decimal("32"), Decimal("31.9"), "live", NOW),
    ]
    book = PriceBook()
    for quote in quotes:
        if quote.symbol in leave_out:
            continue
        if without_previous.get(quote.symbol.replace(".", "_")):
            quote = Quote(quote.symbol, quote.price, None, quote.basis, quote.at)
        book.put(quote)
    return book


def test_values_weights_profit_and_change_in_taiwan_dollars() -> None:
    result = valuation(HOLDINGS, _book())

    rows = {row.symbol: row for row in result.holdings}
    # 2000 x 1480; NVIDIA at 180 dollars and 32 Taiwan dollars a dollar.
    assert rows["2330.TW"].value == Decimal("2960000.00")
    assert rows["NVDA"].value == Decimal("864000.00")
    assert rows["CASH"].value == Decimal("600000.00")
    assert result.total_value == Decimal("4424000.00")
    assert [rows[symbol].weight for symbol in ("2330.TW", "NVDA", "CASH")] == [
        Decimal("66.91"),
        Decimal("19.53"),
        Decimal("13.56"),
    ]
    assert rows["2330.TW"].profit == Decimal("-1000000.00")
    assert rows["2330.TW"].profit_percent == Decimal("-25.25")
    # Cost converted at today's rate: 150 x 142.3 x 32.
    assert rows["NVDA"].profit == Decimal("180960.00")
    assert rows["NVDA"].profit_percent == Decimal("26.49")
    assert rows["CASH"].price is None and rows["CASH"].profit is None
    assert result.profit == Decimal("-819040.00")
    assert result.profit_percent == Decimal("-17.64")
    # 2000 x -15 and 150 x 5 x 32.
    assert result.change == Decimal("-6000.00")
    assert result.change_percent == Decimal("-0.14")
    assert result.left_out == []
    assert result.change_left_out == []


def test_the_shares_add_up_to_100() -> None:
    result = valuation(HOLDINGS, _book())

    shares = [row.weight for row in result.holdings if row.weight is not None]
    assert sum(shares) == Decimal("100.00")


def test_a_missing_price_is_missing_not_zero_and_left_out_of_the_totals() -> None:
    result = valuation(HOLDINGS, _book("2330.TW"))

    row = result.holdings[0]
    assert (row.price, row.value, row.weight, row.profit) == (None, None, None, None)
    assert result.left_out == ["2330.TW"]
    assert result.total_value == Decimal("1464000.00")
    assert result.profit == Decimal("180960.00")
    assert result.quotes[0].price is None and result.quotes[0].at is None


def test_without_the_exchange_rate_the_us_holdings_are_left_out() -> None:
    result = valuation(HOLDINGS, _book("TWD=X"))

    assert result.left_out == ["NVDA"]
    assert result.total_value == Decimal("3560000.00")


def test_a_currency_without_a_rate_is_left_out_not_valued_at_a_guess() -> None:
    yen = _holding("7203.T", None, "JPY", "100", "2500")

    result = valuation([*HOLDINGS, yen], _book())

    assert result.left_out == ["7203.T"]


def test_a_holding_without_a_previous_close_is_left_out_of_the_change_and_named() -> (
    None
):
    result = valuation(HOLDINGS, _book(NVDA=True))

    # TSMC alone: 2000 x -15, of what TSMC and cash were worth at the previous close.
    assert result.change == Decimal("-30000.00")
    assert result.change_percent == Decimal("-0.84")
    assert result.change_left_out == ["NVDA"]
    # NVIDIA still counts in the value; only its change is not known.
    assert result.total_value == Decimal("4424000.00")


def test_no_previous_close_at_all_leaves_the_change_missing() -> None:
    result = valuation(HOLDINGS, _book(NVDA=True, **{"2330_TW": True}))

    assert result.change is None and result.change_percent is None
    assert result.change_left_out == ["2330.TW", "NVDA"]


def test_nothing_priced_leaves_only_cash() -> None:
    result = valuation(HOLDINGS, PriceBook())

    assert result.total_value == Decimal("600000.00")
    assert result.left_out == ["2330.TW", "NVDA"]
    assert result.profit is None and result.prices_at is None
    assert result.holdings[2].weight == Decimal("100.00")


def test_the_quotes_list_the_holdings_then_the_index_and_the_rate_with_their_delay() -> (
    None
):
    result = valuation(HOLDINGS, _book())

    assert [(q.symbol, q.delay_minutes) for q in result.quotes] == [
        ("2330.TW", 20),
        ("NVDA", 0),
        ("^SOX", 0),
        ("TWD=X", 0),
    ]
    by_symbol = {quote.symbol: quote for quote in result.quotes}
    assert by_symbol["2330.TW"].change_percent == Decimal("-1.00")
    assert by_symbol["^SOX"].price is None
    assert by_symbol["NVDA"].at == PriceTime(
        basis="daily", time=None, day=US_DAY.date()
    )
    assert result.prices_at == PriceTime(basis="live", time=NOW, day=None)
    assert result.source.name == "Yahoo Finance"


def test_prices_are_read_for_every_holding_but_cash_and_the_reference_series() -> None:
    assert priced_symbols(HOLDINGS) == ["2330.TW", "NVDA", "^SOX", "TWD=X"]
