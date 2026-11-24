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

# Why a strategy request was refused.
StrategyErrorCode = Literal[
    "profile_missing", "proposal_not_found", "proposal_not_open"
]


class StrategyErrorDetail(BaseModel):
    code: StrategyErrorCode
    message: str


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


class ProposalView(BaseModel):
    id: int
    created_at: datetime
    question: str
    program: Program
    status: ProposalStatus
    rows: list[DiffRow]
    reasons: list[Reason]
    # The sources the reasons cite, so they can be named after the answer is gone.
    sources: list[Source]


class StoredStrategy(BaseModel):
    """The strategy as the database keeps it, before prices."""

    holdings: list[HoldingView]
    targets: list[TargetRow]
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


class ProposalRefusal(BaseModel):
    code: RefusalCode
    message: str


class ProposalEvent(BaseModel):
    """What came of a revision question: the checked proposal, or why it was refused. Both are
    none when the program made no proposal."""

    proposal: ProposalView | None = None
    refused: ProposalRefusal | None = None
