"""What the strategy endpoints take and send, and the proposal event of the chat stream."""

from datetime import datetime
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


class StrategyView(BaseModel):
    holdings: list[HoldingView]
    targets: list[TargetRow]
    # The proposal waiting for the person; none when there is none.
    proposal: ProposalView | None
    # Says the profile is a simulated sample and nothing on the screen is investment advice.
    notice: Localized


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
