"""Loads the simulated sample profile into the database when it has none.

The sample sits in the repository, so a fresh clone shows a strategy with no other step. It is
checked before it is written: a holding without a target, targets that do not add up to 100, or a
rule of a kind the service does not know stop the load with the reason.
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import func, select

from chat_bridge.chat.sources import Localized
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError
from chat_bridge.strategy.models import (
    ProfileHolding,
    StrategyRule,
    StrategyTarget,
)
from chat_bridge.strategy.schemas import Market, RuleKind
from chat_bridge.strategy.store import transaction

SAMPLE_PROFILE = PROJECT_ROOT / "data" / "profile" / "sample.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SampleHolding(_Strict):
    symbol: str
    names: Localized
    market: Market | None
    currency: str
    # Text, so the amounts are exact; strict mode would refuse a JSON number for a Decimal.
    quantity: Decimal = Field(strict=False)
    average_cost: Decimal = Field(strict=False)


class SampleRule(_Strict):
    kind: RuleKind
    limit_percent: int = Field(ge=0, le=100)
    market: Market | None
    enabled: bool


class SampleProfile(_Strict):
    about: str
    holdings: list[SampleHolding] = Field(min_length=1)
    targets: dict[str, int]
    rules: list[SampleRule]

    @model_validator(mode="after")
    def _targets_match_holdings(self) -> Self:
        symbols = [holding.symbol for holding in self.holdings]
        if sorted(symbols) != sorted(self.targets):
            raise ValueError("every holding needs a target, and only holdings have one")
        if len(set(symbols)) != len(symbols):
            raise ValueError("a holding is listed twice")
        if any(not 0 <= percent <= 100 for percent in self.targets.values()):
            raise ValueError("a target is outside 0 to 100")
        if sum(self.targets.values()) != 100:
            raise ValueError("the targets do not add up to 100")
        return self


class SampleProfileError(LocalSetupError):
    """The sample profile file cannot be read or does not pass its checks."""


def read_sample(path: Path = SAMPLE_PROFILE) -> SampleProfile:
    try:
        return SampleProfile.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, ValidationError) as error:
        raise SampleProfileError(
            f"cannot load the sample profile {path}: {error}"
        ) from error


async def load_sample_if_empty(path: Path = SAMPLE_PROFILE) -> bool:
    """Write the sample into the empty profile tables; leave a profile that exists alone.

    Returns whether it was written.
    """
    sample = read_sample(path)
    async with transaction() as session:
        if await session.scalar(select(func.count()).select_from(ProfileHolding)):
            return False
        for position, holding in enumerate(sample.holdings):
            session.add(
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
        for symbol, percent in sample.targets.items():
            session.add(StrategyTarget(symbol=symbol, percent=percent))
        for position, rule in enumerate(sample.rules):
            session.add(
                StrategyRule(
                    kind=rule.kind,
                    limit_percent=rule.limit_percent,
                    market=rule.market,
                    enabled=rule.enabled,
                    position=position,
                )
            )
    return True
