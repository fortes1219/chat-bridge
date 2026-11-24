"""The strategy's tables, in the knowledge base's database.

They sit beside the knowledge base, in their own tables: a local single-user demo keeps one
database. They are created with the other tables, so a database made by another version is
reported as the knowledge base's tables are.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from chat_bridge.database import Base

# The holding that stands for the cash of the profile. Its quantity is the amount, in its currency.
CASH = "CASH"
# A proposal waiting for the person. The open one is read through a partial index with exactly this
# condition, so finding it does not scan every proposal ever made.
OPEN = "open"
OPEN_CONDITION = "status = 'open'"


class ProfileHolding(Base):
    """One holding of the profile, cash included, in the order the screen lists them."""

    __tablename__ = "profile_holdings"

    symbol: Mapped[str] = mapped_column(primary_key=True)
    # The name in each language the page shows.
    names: Mapped[dict[str, str]] = mapped_column(JSONB)
    # TW or US; none for cash, which belongs to no market.
    market: Mapped[str | None] = mapped_column()
    currency: Mapped[str] = mapped_column()
    quantity: Mapped[Decimal] = mapped_column(Numeric)
    average_cost: Mapped[Decimal] = mapped_column(Numeric)
    position: Mapped[int] = mapped_column()


class StrategyTarget(Base):
    """The current target weight of one holding, in whole percents."""

    __tablename__ = "strategy_targets"

    symbol: Mapped[str] = mapped_column(
        ForeignKey("profile_holdings.symbol"), primary_key=True
    )
    percent: Mapped[int] = mapped_column()


class StrategyRule(Base):
    """A limit the person set on the target weights."""

    __tablename__ = "strategy_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column()
    limit_percent: Mapped[int] = mapped_column()
    # The market a market rule is about; none for the other kinds.
    market: Mapped[str | None] = mapped_column()
    enabled: Mapped[bool] = mapped_column()
    position: Mapped[int] = mapped_column()


class StrategyProposal(Base):
    """A revised strategy an answering program handed back, and what the person did with it.

    It keeps the checked targets, so accepting applies what the service checked, never targets a
    page sends; and the sources its reasons cite, so the screen can name them after a reload.
    """

    __tablename__ = "strategy_proposals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    question: Mapped[str] = mapped_column()
    program: Mapped[str] = mapped_column()
    # Symbol to whole percent, for every holding and cash.
    targets: Mapped[dict[str, int]] = mapped_column(JSONB)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "ix_strategy_proposals_open", "id", postgresql_where=text(OPEN_CONDITION)
        ),
    )
