"""Reading and writing the profile, its targets and the proposals.

A proposal is kept with the targets the service checked. Accepting applies those, never targets
a page sends, and only while the proposal is the open one; the proposal row is locked for the
decision, so two clicks cannot both apply it.
"""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import get_args

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chat_bridge.chat.programs import Program
from chat_bridge.chat.sources import Language, Localized, Source
from chat_bridge.database import create_tables, open_engine
from chat_bridge.strategy.compute import diff_rows, rule_checks, target_rows
from chat_bridge.strategy.models import (
    CASH,
    OPEN,
    OPEN_CONDITION,
    ProfileHolding,
    StrategyProposal,
    StrategyRule,
    StrategyTarget,
)
from chat_bridge.strategy.proposal import CheckedProposal
from chat_bridge.strategy.schemas import (
    Decision,
    HoldingInput,
    HoldingsRequest,
    HoldingView,
    Market,
    ProposalView,
    RuleInput,
    RuleView,
    StoredStrategy,
    StrategyErrorCode,
)

# Said on the screen and in every strategy response: the profile is made up for the demo.
SAMPLE_NOTICE: Localized = {
    "zh-TW": "這是模擬的範例投資組合，畫面上的內容都不是投資建議。",
    "en": "This is a simulated sample portfolio. Nothing on this screen is investment advice.",
}
# What each decision makes of the open proposal.
STATUS_AFTER: dict[Decision, str] = {"accept": "accepted", "reject": "rejected"}
# The kinds a saved rule may be, each with whether it is about a market and so must name one;
# the others must name none. A test keeps its keys the same as RuleKind's.
NAMES_A_MARKET: dict[str, bool] = {
    "max_holding_weight": False,
    "min_holding_weight": False,
    "max_market_weight": True,
}
# The markets a market rule may name, and the limits a rule may set, in whole percents.
MARKETS: frozenset[str] = frozenset(get_args(Market))
LIMIT_RANGE = range(0, 101)
# The listings a holding may be, as Yahoo Finance writes their symbols, each with its market: a
# Taiwan code of four to six digits, with a letter for some ETFs, on the exchange (.TW) or OTC
# (.TWO); a US ticker of one to five letters, with a share class after a dash. Every other symbol,
# another market's suffix, an index (^), a currency pair (=X) or a coin (-USD), is refused: the
# service has the rates and rules of these two markets only.
LISTINGS: tuple[tuple[re.Pattern[str], Market], ...] = (
    (re.compile(r"\d{4,6}[A-Z]?\.TWO?"), "TW"),
    (re.compile(r"[A-Z]{1,5}(-[A-Z])?"), "US"),
)
CURRENCY_OF: dict[Market, str] = {"TW": "TWD", "US": "USD"}
# Every holding is handed to the answering program with each question, and each has its own live
# price subscription, so their number is bounded; so are a name's length and every amount.
MOST_HOLDINGS = 30
LONGEST_NAME = 40
LARGEST_AMOUNT = Decimal("1e15")
LANGUAGES: tuple[Language, ...] = get_args(Language)
# What the cash holding is worth per unit: its quantity is the amount, in Taiwan dollars.
CASH_UNIT = Decimal(1)


class StrategyError(Exception):
    """A strategy request that cannot be done; the code says why, for the page."""

    code: StrategyErrorCode = "profile_missing"
    # The place in the list, from 1, of the item the refusal is about; none for the whole request.
    item: int | None = None


class ProfileMissingError(StrategyError):
    code = "profile_missing"

    def __init__(self) -> None:
        super().__init__("the profile has not been loaded")


class ProposalNotFoundError(StrategyError):
    code = "proposal_not_found"

    def __init__(self, proposal_id: int) -> None:
        super().__init__(f"there is no proposal {proposal_id}")


class ProposalNotOpenError(StrategyError):
    code = "proposal_not_open"

    def __init__(self, proposal_id: int, status: str) -> None:
        super().__init__(f"proposal {proposal_id} is {status}, not open")


class RuleRefusedError(StrategyError):
    """A saved rule the service cannot check; the code says what is wrong with it."""

    def __init__(self, code: StrategyErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class HoldingRefusedError(StrategyError):
    """A saved holding the service cannot keep; the code says what is wrong with it, and `item`
    which holding, when it is about one."""

    def __init__(
        self, code: StrategyErrorCode, message: str, item: int | None = None
    ) -> None:
        super().__init__(message if item is None else f"holding {item}: {message}")
        self.code = code
        self.item = item


@dataclass(frozen=True)
class Profile:
    """The profile as the service reads it: holdings in order, current targets, and rules."""

    holdings: list[HoldingView]
    targets: dict[str, int]
    rules: list[RuleView]

    @property
    def symbols(self) -> list[str]:
        return [holding.symbol for holding in self.holdings]


@asynccontextmanager
async def transaction() -> AsyncIterator[AsyncSession]:
    """One transaction on the app database."""
    async with open_engine() as engine:
        await create_tables(engine)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session, session.begin():
            yield session


async def _read_profile(session: AsyncSession) -> Profile:
    holdings = (
        await session.scalars(select(ProfileHolding).order_by(ProfileHolding.position))
    ).all()
    if not holdings:
        raise ProfileMissingError()
    targets = (await session.scalars(select(StrategyTarget))).all()
    rules = (
        await session.scalars(select(StrategyRule).order_by(StrategyRule.position))
    ).all()
    return Profile(
        # Validated, so a market, a rule kind or a name language the code does not know is
        # refused here.
        holdings=[HoldingView.model_validate(holding) for holding in holdings],
        targets={target.symbol: target.percent for target in targets},
        rules=[
            RuleView.model_validate(
                {
                    "kind": rule.kind,
                    "limit_percent": rule.limit_percent,
                    "market": rule.market,
                    "enabled": rule.enabled,
                }
            )
            for rule in rules
        ],
    )


def _proposal_view(row: StrategyProposal, profile: Profile) -> ProposalView:
    # Validated, so a stored status or program the code does not know is refused here. The rules
    # are checked when the proposal is read, so they are the person's current rules.
    return ProposalView.model_validate(
        {
            "id": row.id,
            "created_at": row.created_at,
            "question": row.question,
            "program": row.program,
            "status": row.status,
            "rows": diff_rows(profile.symbols, profile.targets, row.targets),
            "rule_checks": rule_checks(profile.rules, profile.holdings, row.targets),
            "reasons": row.reasons,
            "sources": row.sources,
        }
    )


async def _open_proposal(session: AsyncSession) -> StrategyProposal | None:
    # The condition is the partial index's own text, so the planner reads the index.
    return (
        await session.scalars(
            select(StrategyProposal)
            .where(text(OPEN_CONDITION))
            .order_by(StrategyProposal.id.desc())
            .limit(1)
        )
    ).first()


async def _stored_strategy(session: AsyncSession) -> StoredStrategy:
    profile = await _read_profile(session)
    open_row = await _open_proposal(session)
    return StoredStrategy(
        holdings=profile.holdings,
        targets=target_rows(profile.symbols, profile.targets),
        targets_total=sum(profile.targets.values()),
        rule_checks=rule_checks(profile.rules, profile.holdings, profile.targets),
        proposal=None if open_row is None else _proposal_view(open_row, profile),
        notice=SAMPLE_NOTICE,
    )


async def read_profile() -> Profile:
    """The profile, for the model's input and for checking a proposal."""
    async with transaction() as session:
        return await _read_profile(session)


async def read_strategy() -> StoredStrategy:
    """The current strategy and the open proposal. Raises ProfileMissingError."""
    async with transaction() as session:
        return await _stored_strategy(session)


async def save_proposal(
    question: str, program: Program, checked: CheckedProposal, sources: list[Source]
) -> ProposalView:
    """Keep a checked proposal as the open one; the proposal it replaces is marked so."""
    async with transaction() as session:
        profile = await _read_profile(session)
        await session.execute(
            update(StrategyProposal)
            .where(text(OPEN_CONDITION))
            .values(status="replaced", decided_at=datetime.now(UTC))
        )
        row = StrategyProposal(
            question=question,
            program=program.value,
            targets=checked.targets,
            reasons=[reason.model_dump() for reason in checked.reasons],
            sources=[source.model_dump(mode="json") for source in sources],
            status=OPEN,
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return _proposal_view(row, profile)


async def decide(proposal_id: int, decision: Decision) -> StoredStrategy:
    """Accept or reject the open proposal, and return the strategy after it.

    Accepting makes the proposal's stored targets the current ones. Raises ProposalNotFoundError
    or ProposalNotOpenError, and changes nothing then.
    """
    async with transaction() as session:
        row = (
            await session.scalars(
                select(StrategyProposal)
                .where(StrategyProposal.id == proposal_id)
                .with_for_update()
            )
        ).first()
        if row is None:
            raise ProposalNotFoundError(proposal_id)
        if row.status != OPEN:
            raise ProposalNotOpenError(proposal_id, row.status)
        if decision == "accept":
            for symbol, percent in row.targets.items():
                await session.execute(
                    update(StrategyTarget)
                    .where(StrategyTarget.symbol == symbol)
                    .values(percent=percent)
                )
        row.status = STATUS_AFTER[decision]
        row.decided_at = datetime.now(UTC)
        await session.flush()
        return await _stored_strategy(session)


def _rule_problem(rule: RuleInput) -> tuple[StrategyErrorCode, str] | None:
    """What is wrong with one rule, or None. The first thing wrong is the one named."""
    needs_market = NAMES_A_MARKET.get(rule.kind)
    if needs_market is None:
        return "rule_unknown_kind", f"{rule.kind} is not a kind of rule"
    if rule.limit_percent not in LIMIT_RANGE:
        return "rule_limit_out_of_range", f"{rule.limit_percent}% is outside 0 to 100"
    if needs_market and rule.market not in MARKETS:
        return "rule_market", f"a {rule.kind} rule names TW or US, not {rule.market}"
    if not needs_market and rule.market is not None:
        return "rule_market", f"a {rule.kind} rule names no market"
    return None


def check_rules(rules: list[RuleInput]) -> list[RuleView]:
    """The rules as the service keeps them. Raises RuleRefusedError, naming the rule by its
    place in the list, for the first one that is not a known kind with a limit from 0 to 100 and
    the market its kind needs."""
    for number, rule in enumerate(rules, start=1):
        problem = _rule_problem(rule)
        if problem is not None:
            code, message = problem
            raise RuleRefusedError(code, f"rule {number}: {message}")
    return [RuleView.model_validate(rule.model_dump()) for rule in rules]


async def save_rules(rules: list[RuleInput]) -> StoredStrategy:
    """Replace the saved rules with these, in this order, and return the strategy after it.

    Raises RuleRefusedError, or ProfileMissingError, and changes nothing then.
    """
    checked = check_rules(rules)
    async with transaction() as session:
        await _read_profile(session)
        await session.execute(delete(StrategyRule))
        session.add_all(
            StrategyRule(
                kind=rule.kind,
                limit_percent=rule.limit_percent,
                market=rule.market,
                enabled=rule.enabled,
                position=position,
            )
            for position, rule in enumerate(checked)
        )
        await session.flush()
        return await _stored_strategy(session)


def market_of(symbol: str) -> Market | None:
    """The market a symbol is listed in, or None for a symbol of no listing the service keeps."""
    return next(
        (market for pattern, market in LISTINGS if pattern.fullmatch(symbol)), None
    )


def _amount_in_range(amount: Decimal, *, above_zero: bool) -> bool:
    if not amount.is_finite() or amount > LARGEST_AMOUNT:
        return False
    return amount > 0 if above_zero else amount >= 0


def _holding_problem(
    holding: HoldingInput, seen: set[str]
) -> tuple[StrategyErrorCode, str] | None:
    """What is wrong with one holding of a known listing, or None. The first thing wrong is the
    one named."""
    symbol = holding.symbol
    if symbol in seen:
        return "holding_repeated", f"{symbol} is listed more than once"
    names = [holding.names.get(language, "").strip() for language in LANGUAGES]
    if not all(names) or any(len(name) > LONGEST_NAME for name in names):
        return (
            "holding_name",
            f"{symbol} needs a name of 1 to {LONGEST_NAME} characters",
        )
    if not _amount_in_range(holding.quantity, above_zero=True):
        return (
            "holding_amount",
            f"the quantity of {symbol} is not above 0 and at most 1e15",
        )
    if not _amount_in_range(holding.average_cost, above_zero=False):
        return "holding_amount", f"the average cost of {symbol} is not 0 to 1e15"
    return None


def check_holdings(request: HoldingsRequest) -> list[HoldingView]:
    """The holdings as the service keeps them, each with the market and currency its symbol
    says, cash last. Raises HoldingRefusedError for more than MOST_HOLDINGS holdings; for cash
    outside 0 to 1e15; and, naming the holding by its place in the list, for the first one that
    is not a Taiwan or US listing, is listed twice, has no name or a long one, or an amount out of
    range."""
    if len(request.holdings) > MOST_HOLDINGS:
        raise HoldingRefusedError(
            "holdings_too_many", f"at most {MOST_HOLDINGS} holdings besides cash"
        )
    if not _amount_in_range(request.cash, above_zero=False):
        raise HoldingRefusedError("holding_amount", "the cash is not 0 to 1e15")
    seen: set[str] = set()
    kept: list[HoldingView] = []
    for number, holding in enumerate(request.holdings, start=1):
        holding = holding.model_copy(update={"symbol": holding.symbol.strip().upper()})
        market = market_of(holding.symbol)
        # The cash's own symbol reads as a US ticker, but cash is set apart.
        if market is None or holding.symbol == CASH:
            raise HoldingRefusedError(
                "holding_symbol",
                f"{holding.symbol!r} is not a Taiwan listing ending in .TW or .TWO, or a US "
                "ticker",
                number,
            )
        problem = _holding_problem(holding, seen)
        if problem is not None:
            code, message = problem
            raise HoldingRefusedError(code, message, number)
        seen.add(holding.symbol)
        kept.append(
            HoldingView(
                symbol=holding.symbol,
                names={
                    language: holding.names[language].strip() for language in LANGUAGES
                },
                market=market,
                currency=CURRENCY_OF[market],
                quantity=holding.quantity,
                average_cost=holding.average_cost,
            )
        )
    return kept


async def save_holdings(request: HoldingsRequest) -> StoredStrategy:
    """Replace the holdings with these, in this order, and set the cash; return the strategy after
    it.

    A kept holding keeps its target, a new one gets 0, a removed one loses its target. The open
    proposal was checked against the holdings before, so it is closed as replaced. Raises
    HoldingRefusedError, or ProfileMissingError, and changes nothing then.
    """
    holdings = check_holdings(request)
    async with transaction() as session:
        profile = await _read_profile(session)
        cash = next((held for held in profile.holdings if held.symbol == CASH), None)
        if cash is None:
            raise ProfileMissingError()
        saved = {holding.symbol for holding in holdings}
        removed = [symbol for symbol in profile.symbols if symbol not in saved | {CASH}]
        # The targets first: each points at its holding.
        await session.execute(
            delete(StrategyTarget).where(StrategyTarget.symbol.in_(removed))
        )
        await session.execute(
            delete(ProfileHolding).where(ProfileHolding.symbol.in_(removed))
        )
        cash_row = cash.model_copy(
            update={"quantity": request.cash, "average_cost": CASH_UNIT}
        )
        for position, holding in enumerate([*holdings, cash_row]):
            # Field by field: dumping the view would turn the amounts into text.
            await session.merge(
                ProfileHolding(
                    symbol=holding.symbol,
                    names=holding.names,
                    market=holding.market,
                    currency=holding.currency,
                    quantity=holding.quantity,
                    average_cost=holding.average_cost,
                    position=position,
                )
            )
        await session.flush()
        session.add_all(
            StrategyTarget(symbol=holding.symbol, percent=0)
            for holding in holdings
            if holding.symbol not in profile.targets
        )
        await session.execute(
            update(StrategyProposal)
            .where(text(OPEN_CONDITION))
            .values(status="replaced", decided_at=datetime.now(UTC))
        )
        await session.flush()
        return await _stored_strategy(session)
