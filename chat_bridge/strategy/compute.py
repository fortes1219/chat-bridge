"""The numbers of the strategy screen, computed by the service and never taken from a model."""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from chat_bridge.chat.sources import Localized
from chat_bridge.strategy.models import CASH
from chat_bridge.strategy.prices import SOURCE_NAME, PriceBook, Quote
from chat_bridge.strategy.schemas import (
    DiffRow,
    HoldingValue,
    HoldingView,
    Market,
    PriceSourceView,
    PriceTime,
    QuoteView,
    RuleCheck,
    RuleChecks,
    RuleKind,
    RuleView,
    TargetRow,
    Valuation,
)

# Money and percents are shown to the cent.
CENT = Decimal("0.01")
ZERO = Decimal(0)
# The series whose price is one unit of a currency in Taiwan dollars; none for Taiwan dollars.
# A currency not listed has no rate, so its holdings are left out, never valued at a guess.
RATE_SYMBOL: dict[str, str | None] = {"TWD": None, "USD": "TWD=X"}
# Shown beside the holdings: the index the sample news follows, and the rate the US holdings
# are valued at.
REFERENCE_SERIES: dict[str, Localized] = {
    "^SOX": {"zh-TW": "費城半導體指數", "en": "PHLX Semiconductor Index"},
    "TWD=X": {"zh-TW": "美元兌新台幣", "en": "US dollar in Taiwan dollars"},
}
# Yahoo's stated delay of each market's quotes, in minutes (help.yahoo.com, "Exchanges and data
# providers on Yahoo Finance"): the Taiwan Stock Exchange 20 minutes, Nasdaq real time. The
# sample's US holdings trade on Nasdaq.
MARKET_DELAY_MINUTES: dict[str, int] = {"TW": 20, "US": 0}
# The same for the reference series: the index comes through Nasdaq's index data service and
# currency rates through ICE Data Services, both in real time.
REFERENCE_DELAY_MINUTES: dict[str, int] = {"^SOX": 0, "TWD=X": 0}
PRICE_TERMS_URL = "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html"


def target_rows(symbols: list[str], current: dict[str, int]) -> list[TargetRow]:
    """The current target of each holding, in the profile's order."""
    return [TargetRow(symbol=symbol, current=current[symbol]) for symbol in symbols]


def diff_rows(
    symbols: list[str], current: dict[str, int], proposed: dict[str, int]
) -> list[DiffRow]:
    """Current, proposed and change for each holding, in the profile's order."""
    return [
        DiffRow(
            symbol=symbol,
            current=current[symbol],
            proposed=proposed[symbol],
            change=proposed[symbol] - current[symbol],
        )
        for symbol in symbols
    ]


# The market of each holding; none for cash.
Markets = dict[str, Market | None]


@dataclass(frozen=True)
class _Measure:
    """What a rule looks at on a set of targets, and the holdings that break it."""

    measured: int | None
    breaking: list[str]


def _max_holding(rule: RuleView, weights: dict[str, int], markets: Markets) -> _Measure:
    if not weights:
        return _Measure(None, [])
    over = [symbol for symbol, weight in weights.items() if weight > rule.limit_percent]
    return _Measure(max(weights.values()), over)


def _min_holding(rule: RuleView, weights: dict[str, int], markets: Markets) -> _Measure:
    # A target of 0 means the strategy holds none of it, so the rule does not apply to it.
    held = {symbol: weight for symbol, weight in weights.items() if weight > 0}
    if not held:
        return _Measure(None, [])
    under = [symbol for symbol, weight in held.items() if weight < rule.limit_percent]
    return _Measure(min(held.values()), under)


def _max_market(rule: RuleView, weights: dict[str, int], markets: Markets) -> _Measure:
    members = [symbol for symbol in weights if markets[symbol] == rule.market]
    total = sum(weights[symbol] for symbol in members)
    return _Measure(total, members if total > rule.limit_percent else [])


# What each kind of rule looks at. A target exactly at the limit meets it.
RULE_MEASURES: dict[
    RuleKind, Callable[[RuleView, dict[str, int], Markets], _Measure]
] = {
    "max_holding_weight": _max_holding,
    "min_holding_weight": _min_holding,
    "max_market_weight": _max_market,
}


def _rule_check(rule: RuleView, weights: dict[str, int], markets: Markets) -> RuleCheck:
    if not rule.enabled:
        return RuleCheck(**rule.model_dump(), met=None, measured=None, breaking=[])
    measure = RULE_MEASURES[rule.kind](rule, weights, markets)
    return RuleCheck(
        **rule.model_dump(),
        met=not measure.breaking,
        measured=measure.measured,
        breaking=measure.breaking,
    )


def rule_checks(
    rules: list[RuleView], holdings: list[HoldingView], targets: dict[str, int]
) -> RuleChecks:
    """Each rule's result on the given target weights, and how many of the rules that are on
    are met.

    The rules limit what the strategy puts in each holding and in each market, so cash, which is
    neither, is not a holding they look at.
    """
    weights = {
        holding.symbol: targets[holding.symbol]
        for holding in holdings
        if holding.symbol != CASH
    }
    markets = {holding.symbol: holding.market for holding in holdings}
    checks = [_rule_check(rule, weights, markets) for rule in rules]
    enabled = [check for check in checks if check.enabled]
    return RuleChecks(
        met=sum(check.met is True for check in enabled),
        enabled=len(enabled),
        rules=checks,
    )


def priced_symbols(holdings: list[HoldingView]) -> list[str]:
    """The series the prices are read for: every holding but cash, then the reference series."""
    symbols = [holding.symbol for holding in holdings if holding.symbol != CASH]
    return symbols + [symbol for symbol in REFERENCE_SERIES if symbol not in symbols]


def price_time(quote: Quote) -> PriceTime:
    if quote.basis == "live":
        return PriceTime(basis="live", time=quote.at, day=None)
    return PriceTime(basis="daily", time=None, day=quote.at.date())


def _rate(currency: str, book: PriceBook) -> Decimal | None:
    """One unit of the currency in Taiwan dollars; none when it cannot be had."""
    if currency not in RATE_SYMBOL:
        return None
    symbol = RATE_SYMBOL[currency]
    if symbol is None:
        return Decimal(1)
    quote = book.get(symbol)
    return None if quote is None else quote.price


def _percent(part: Decimal, whole: Decimal) -> Decimal | None:
    return None if whole == 0 else (part / whole * 100).quantize(CENT)


def _change_percent(quote: Quote) -> Decimal | None:
    if quote.previous_close is None:
        return None
    return _percent(quote.price - quote.previous_close, quote.previous_close)


@dataclass(frozen=True)
class _Valued:
    """A holding valued at its latest price, in Taiwan dollars, before rounding."""

    symbol: str
    value: Decimal
    # None for cash, which has no cost, profit or price.
    quote: Quote | None = None
    cost: Decimal = Decimal(0)
    # Since the previous close; none when the quote does not say it.
    change: Decimal | None = Decimal(0)


def _value(holding: HoldingView, book: PriceBook) -> _Valued | None:
    """The holding in Taiwan dollars at the current rate; none without a price or rate.

    The profile keeps no rate from the day a US holding was bought, so its cost is converted at
    today's rate too; its profit is the price's move, not the currency's.
    """
    rate = _rate(holding.currency, book)
    if rate is None:
        return None
    if holding.symbol == CASH:
        return _Valued(symbol=CASH, value=holding.quantity * rate)
    quote = book.get(holding.symbol)
    if quote is None:
        return None
    previous = quote.previous_close
    return _Valued(
        symbol=holding.symbol,
        value=holding.quantity * quote.price * rate,
        quote=quote,
        cost=holding.quantity * holding.average_cost * rate,
        change=None
        if previous is None
        else holding.quantity * (quote.price - previous) * rate,
    )


def _holding_value(valued: _Valued | None, symbol: str, total: Decimal) -> HoldingValue:
    if valued is None:
        return HoldingValue(
            symbol=symbol,
            price=None,
            value=None,
            weight=None,
            profit=None,
            profit_percent=None,
        )
    profit = None if valued.quote is None else valued.value - valued.cost
    return HoldingValue(
        symbol=symbol,
        price=None if valued.quote is None else valued.quote.price,
        value=valued.value.quantize(CENT),
        weight=_percent(valued.value, total),
        profit=None if profit is None else profit.quantize(CENT),
        profit_percent=None if profit is None else _percent(profit, valued.cost),
    )


def _quote_view(
    symbol: str, names: Localized, delay: int | None, book: PriceBook
) -> QuoteView:
    quote = book.get(symbol)
    return QuoteView(
        symbol=symbol,
        names=names,
        price=None if quote is None else quote.price,
        change_percent=None if quote is None else _change_percent(quote),
        at=None if quote is None else price_time(quote),
        delay_minutes=delay,
    )


def valuation(
    holdings: list[HoldingView], book: PriceBook, *, live: bool = False
) -> Valuation:
    """Values, weights, profit and loss, the change since the previous close and the quotes.

    A holding without a price, or without the rate of its currency, is left out of every total
    and named in `left_out`; the weights are of what is valued. `live` says whether the live
    price stream is open, so the page can say whether prices are following.
    """
    valued = {holding.symbol: _value(holding, book) for holding in holdings}
    counted = [item for item in valued.values() if item is not None]
    priced = [item for item in counted if item.quote is not None]
    total = sum((item.value for item in counted), Decimal(0))
    cost = sum((item.cost for item in priced), Decimal(0))
    profit = sum((item.value - item.cost for item in priced), Decimal(0))
    # The change counts the holdings whose previous close is known; one without it is named
    # instead, as a holding without a price is. Its percent is of what those holdings and cash
    # were worth at the previous closes.
    moving = [item for item in priced if item.change is not None]
    cash = sum((item.value for item in counted if item.quote is None), Decimal(0))
    change = sum((item.change or ZERO for item in moving), ZERO) if moving else None
    before = cash + sum((item.value - (item.change or ZERO) for item in moving), ZERO)
    newest = max(
        (item.quote for item in priced if item.quote), key=lambda q: q.at, default=None
    )
    return Valuation(
        currency="TWD",
        live=live,
        total_value=total.quantize(CENT),
        change=None if change is None else change.quantize(CENT),
        change_percent=None if change is None else _percent(change, before),
        change_left_out=[item.symbol for item in priced if item.change is None],
        profit=profit.quantize(CENT) if priced else None,
        profit_percent=_percent(profit, cost) if priced else None,
        left_out=[symbol for symbol, item in valued.items() if item is None],
        prices_at=None if newest is None else price_time(newest),
        holdings=[
            _holding_value(valued[holding.symbol], holding.symbol, total)
            for holding in holdings
        ],
        quotes=[
            _quote_view(
                holding.symbol,
                holding.names,
                MARKET_DELAY_MINUTES.get(holding.market or ""),
                book,
            )
            for holding in holdings
            if holding.symbol != CASH
        ]
        + [
            _quote_view(symbol, names, REFERENCE_DELAY_MINUTES[symbol], book)
            for symbol, names in REFERENCE_SERIES.items()
            if symbol not in valued
        ],
        source=PriceSourceView(name=SOURCE_NAME, terms_url=PRICE_TERMS_URL),
    )
