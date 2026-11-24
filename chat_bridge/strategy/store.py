"""Reading and writing the profile, its targets and the proposals.

A proposal is kept with the targets the service checked. Accepting applies those, never targets
a page sends, and only while the proposal is the open one; the proposal row is locked for the
decision, so two clicks cannot both apply it.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chat_bridge.chat.programs import Program
from chat_bridge.chat.sources import Localized, Source
from chat_bridge.database import create_tables, open_engine
from chat_bridge.strategy.compute import diff_rows, target_rows
from chat_bridge.strategy.models import (
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
    HoldingView,
    ProposalView,
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


class StrategyError(Exception):
    """A strategy request that cannot be done; the code says why, for the page."""

    code: StrategyErrorCode = "profile_missing"


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


@dataclass(frozen=True)
class Profile:
    """The profile as the service reads it: holdings in order, current targets, and rules."""

    holdings: list[HoldingView]
    targets: dict[str, int]
    rules: list[dict[str, Any]]

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
        # Validated, so a market or a name language the code does not know is refused here.
        holdings=[HoldingView.model_validate(holding) for holding in holdings],
        targets={target.symbol: target.percent for target in targets},
        rules=[
            {
                "kind": rule.kind,
                "limit_percent": rule.limit_percent,
                "market": rule.market,
                "enabled": rule.enabled,
            }
            for rule in rules
        ],
    )


def _proposal_view(row: StrategyProposal, profile: Profile) -> ProposalView:
    # Validated, so a stored status or program the code does not know is refused here.
    return ProposalView.model_validate(
        {
            "id": row.id,
            "created_at": row.created_at,
            "question": row.question,
            "program": row.program,
            "status": row.status,
            "rows": diff_rows(profile.symbols, profile.targets, row.targets),
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
