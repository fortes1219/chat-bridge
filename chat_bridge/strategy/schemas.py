"""What the strategy endpoints take and send, and the proposal event of the chat stream."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, PlainSerializer

from chat_bridge.chat.programs import Program
from chat_bridge.chat.sources import Localized, Source

# An exact amount sent as text in plain notation: the database may hand 20000 back as 2E+4, and
# a page shows the number, not its exponent.
Amount = Annotated[
    Decimal, PlainSerializer(lambda value: format(value, "f"), return_type=str)
]
Market = Literal["TW", "US"]
# The weight limits a person can set, the kinds portfolio optimisers take: a bound on each
# holding's weight, from above and below, and a bound on one market's total.
RuleKind = Literal["max_holding_weight", "min_holding_weight", "max_market_weight"]
ProposalStatus = Literal["open", "accepted", "rejected", "replaced"]
Decision = Literal["accept", "reject"]
# A live price from the stream, or the latest value of the daily series: the day's close once it
# has ended, its latest price while it trades.
Basis = Literal["live", "daily"]

# Why a proposal was refused, for the page to say so in its language. The message beside it is for
# people reading the API or the records.
RefusalCode = Literal[
    "not_the_shape",
    "unknown_holding",
    "repeated_holding",
    "missing_holding",
    "percent_out_of_range",
    "not_100",
    "unknown_source",
]

# Why a strategy request was refused. The rule codes say what is wrong with a rule the person
# saved: a kind the service does not know, a limit outside 0 to 100, or a market that does not
# fit the kind (a market rule names TW or US; the others name none). The holding codes say what is
# wrong with the holdings the person saved: a symbol of no Taiwan or US listing, a symbol listed
# twice, a name empty or too long, an amount out of range, or too many holdings.
StrategyErrorCode = Literal[
    "profile_missing",
    "proposal_not_found",
    "proposal_not_open",
    "rule_unknown_kind",
    "rule_limit_out_of_range",
    "rule_market",
    "holding_symbol",
    "holding_repeated",
    "holding_name",
    "holding_amount",
    "holdings_too_many",
]


class StrategyErrorDetail(BaseModel):
    code: StrategyErrorCode
    message: str
    # The place in the list, from 1, of the holding a refusal is about, so the page can point at
    # it; none when it is about the whole request.
    item: int | None = None


class HoldingView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    names: Localized
    market: Market | None
    currency: str
    quantity: Amount
    average_cost: Amount


class TargetRow(BaseModel):
    symbol: str
    current: int


class DiffRow(BaseModel):
    """One holding of a proposal: its current target, the proposed one, and the change, in whole
    percents. The change is computed here, never taken from the model."""

    symbol: str
    current: int
    proposed: int
    change: int


class Reason(BaseModel):
    text: str
    # The source numbers it rests on, numbered as in the answer.
    sources: list[int]


class RuleView(BaseModel):
    """A limit the person set on the target weights, as the service keeps it."""

    kind: RuleKind
    limit_percent: int
    # The market a market rule is about; none for the other kinds.
    market: Market | None
    enabled: bool


class RuleCheck(RuleView):
    """A rule and its result on one set of target weights, computed by the service."""

    # None when the rule is off.
    met: bool | None
    # The weight the rule looks at, in whole percents: the largest holding's target, the
    # smallest held holding's, or the market's total. None when the rule is off or there is
    # nothing to measure, such as no holding held.
    measured: int | None
    # The holdings that break it: those over or under the limit, or every holding of a market
    # over its limit.
    breaking: list[str]


class RuleChecks(BaseModel):
    """Every rule checked on one set of target weights, and how many of those that are on are
    met."""

    met: int
    enabled: int
    rules: list[RuleCheck]


class ProposalView(BaseModel):
    id: int
    created_at: datetime
    question: str
    program: Program
    status: ProposalStatus
    rows: list[DiffRow]
    # The rules checked on the proposed targets, beside the strategy's own checks of the current
    # ones.
    rule_checks: RuleChecks
    reasons: list[Reason]
    # The sources the reasons cite, so they can be named after the answer is gone.
    sources: list[Source]


class StoredStrategy(BaseModel):
    """The strategy as the database keeps it, before prices."""

    holdings: list[HoldingView]
    targets: list[TargetRow]
    # What the current targets add up to, in whole percents. It is 100 until the person removes a
    # holding whose target was above 0; a proposal the person accepts makes it 100 again.
    targets_total: int
    # The rules checked on the current targets. Prices do not move them.
    rule_checks: RuleChecks
    # The proposal waiting for the person; none when there is none.
    proposal: ProposalView | None
    # Says the profile is a simulated sample and nothing on the screen is investment advice.
    notice: Localized


class PriceTime(BaseModel):
    """When a price is from: a live price's moment, or a daily value's trading day."""

    basis: Basis
    time: datetime | None
    # As the exchange's calendar names it, so it does not move with the reader's time zone.
    day: date | None


class QuoteView(BaseModel):
    symbol: str
    names: Localized
    # In the series' own currency; none when it could not be had.
    price: Amount | None
    # Since the previous close, in percent.
    change_percent: Amount | None
    at: PriceTime | None
    # The source's stated delay for this market; none when it states none.
    delay_minutes: int | None


class HoldingValue(BaseModel):
    """One holding valued at its latest price. Money is in Taiwan dollars; everything is none
    when the holding is left out for a missing price or exchange rate."""

    symbol: str
    # In the holding's own currency; none for cash.
    price: Amount | None
    value: Amount | None
    # Of the total value, in percent.
    weight: Amount | None
    profit: Amount | None
    profit_percent: Amount | None


class PriceSourceView(BaseModel):
    name: str
    terms_url: str


class Valuation(BaseModel):
    """The numbers that follow the prices, all computed by the service."""

    currency: Literal["TWD"]
    # Whether the service's live connection to the price source is open. When it is not, the
    # prices stay as they are, each with its time.
    live: bool
    # The holdings that have a price, and cash.
    total_value: Amount
    # Each valued holding's move since its own previous close, summed; none when no holding has
    # one.
    change: Amount | None
    change_percent: Amount | None
    # Valued holdings whose previous close is not known, left out of the change.
    change_left_out: list[str]
    profit: Amount | None
    profit_percent: Amount | None
    # Holdings without a price or an exchange rate, left out of every total.
    left_out: list[str]
    # The latest of the holdings' prices; none when no holding has one.
    prices_at: PriceTime | None
    holdings: list[HoldingValue]
    # The holdings' prices, then the series shown beside them.
    quotes: list[QuoteView]
    source: PriceSourceView


class StrategyView(StoredStrategy):
    valuation: Valuation


class DecisionRequest(BaseModel):
    """A JSON body, so a form or another web page cannot send a decision without the browser
    asking the service first, which it never allows."""

    model_config = ConfigDict(extra="forbid")

    decision: Decision


class RuleInput(BaseModel):
    """One rule as the page sends it. The kind and the market are plain text here, so one the
    service does not know is refused with its own code, not as a malformed request."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    limit_percent: int
    market: str | None
    enabled: bool


class RulesRequest(BaseModel):
    """Every rule, in the order the screen lists them; they replace the saved ones. A JSON body,
    so a form or another web page cannot send it without the browser asking the service first."""

    model_config = ConfigDict(extra="forbid")

    rules: list[RuleInput]


class HoldingInput(BaseModel):
    """One holding as the page sends it; the service works out its market and currency from the
    symbol."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    names: Localized
    quantity: Decimal
    average_cost: Decimal


class HoldingsRequest(BaseModel):
    """Every holding but cash, in the order the screen lists them, and the cash in Taiwan dollars;
    they replace the saved ones. A JSON body, for the same reason as the rules."""

    model_config = ConfigDict(extra="forbid")

    holdings: list[HoldingInput]
    cash: Decimal


class ProposalRefusal(BaseModel):
    code: RefusalCode
    message: str


class ProposalEvent(BaseModel):
    """What came of a revision question: the checked proposal, or why it was refused. Both are
    none when the program made no proposal."""

    proposal: ProposalView | None = None
    refused: ProposalRefusal | None = None
