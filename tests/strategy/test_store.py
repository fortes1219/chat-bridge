"""The profile, its targets and the proposals in the embedded database.

Each test gets a database of its own with the repository's sample profile loaded, so the tests are
marked slow. No program and no embedding model is used.
"""

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from chat_bridge.chat.programs import Program
from chat_bridge.chat.sources import Source
from chat_bridge.strategy import store
from chat_bridge.strategy.prices import Quote
from chat_bridge.strategy.proposal import CheckedProposal
from chat_bridge.strategy.sample import load_sample_if_empty, read_sample
from chat_bridge.strategy.schemas import (
    HoldingInput,
    HoldingsRequest,
    Reason,
    RuleInput,
    StrategyView,
)
from chat_bridge.strategy.state import StrategyState
from tests.utils import prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

SAMPLE = read_sample()
SOURCE = Source(
    number=3,
    file="data/truth/2026-09-16-fomc-raises-rate.md",
    title="聯準會9月升息",
    heading="事件發生",
    event_date=None,
)


def _checked(cash: int) -> CheckedProposal:
    """The sample's targets with `cash` for cash and TSMC taking up the difference."""
    targets = dict(SAMPLE.targets)
    targets["2330.TW"] -= cash - targets["CASH"]
    targets["CASH"] = cash
    return CheckedProposal(
        targets=targets, reasons=[Reason(text="升息", sources=[SOURCE.number])]
    )


def _save(cash: int) -> int:
    view = asyncio.run(
        store.save_proposal("調整配置", Program.CLAUDE_CODE, _checked(cash), [SOURCE])
    )
    return view.id


@pytest.fixture(autouse=True)
def profile(tmp_path: Path) -> Iterator[None]:
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        assert asyncio.run(load_sample_if_empty())
        yield


def test_the_sample_is_loaded_once_in_order_with_exact_amounts() -> None:
    assert not asyncio.run(load_sample_if_empty())

    view = asyncio.run(store.read_strategy())

    assert [holding.symbol for holding in view.holdings] == [
        holding.symbol for holding in SAMPLE.holdings
    ]
    assert {row.symbol: row.current for row in view.targets} == SAMPLE.targets
    assert view.proposal is None
    holdings = view.model_dump(mode="json")["holdings"]
    assert holdings[2]["quantity"] == "20000"
    assert holdings[2]["average_cost"] == "92.4"


def test_a_saved_proposal_is_the_open_one_with_its_change_column() -> None:
    proposal_id = _save(cash=25)

    view = asyncio.run(store.read_strategy())

    assert view.proposal is not None
    assert view.proposal.id == proposal_id
    assert view.proposal.status == "open"
    rows = {row.symbol: row for row in view.proposal.rows}
    assert (rows["CASH"].current, rows["CASH"].proposed, rows["CASH"].change) == (
        10,
        25,
        15,
    )
    assert rows["2330.TW"].change == -15
    assert sum(row.change for row in view.proposal.rows) == 0
    assert view.proposal.sources == [SOURCE]
    # Nothing changes until the person accepts.
    assert {row.symbol: row.current for row in view.targets} == SAMPLE.targets


def test_accepting_makes_the_stored_targets_the_current_ones() -> None:
    proposal_id = _save(cash=25)

    view = asyncio.run(store.decide(proposal_id, "accept"))

    assert {row.symbol: row.current for row in view.targets} == _checked(25).targets
    assert view.proposal is None


def test_rejecting_leaves_the_strategy_as_it_was() -> None:
    proposal_id = _save(cash=25)

    view = asyncio.run(store.decide(proposal_id, "reject"))

    assert {row.symbol: row.current for row in view.targets} == SAMPLE.targets
    assert view.proposal is None


def test_a_new_proposal_replaces_the_open_one_which_can_no_longer_be_accepted() -> None:
    first = _save(cash=25)
    second = _save(cash=15)

    view = asyncio.run(store.read_strategy())
    assert view.proposal is not None
    assert view.proposal.id == second
    with pytest.raises(store.ProposalNotOpenError):
        asyncio.run(store.decide(first, "accept"))
    assert {row.symbol: row.current for row in view.targets} == SAMPLE.targets


def test_a_decided_proposal_cannot_be_decided_again() -> None:
    proposal_id = _save(cash=25)
    asyncio.run(store.decide(proposal_id, "reject"))

    with pytest.raises(store.ProposalNotOpenError):
        asyncio.run(store.decide(proposal_id, "accept"))

    view = asyncio.run(store.read_strategy())
    assert {row.symbol: row.current for row in view.targets} == SAMPLE.targets


def test_a_decision_on_a_proposal_that_does_not_exist_is_refused() -> None:
    with pytest.raises(store.ProposalNotFoundError):
        asyncio.run(store.decide(999, "accept"))


def test_the_sample_rules_are_checked_on_the_current_targets() -> None:
    view = asyncio.run(store.read_strategy())

    checks = view.rule_checks
    assert [rule.kind for rule in checks.rules] == [rule.kind for rule in SAMPLE.rules]
    assert (checks.met, checks.enabled) == (3, 3)


def _rule(kind: str, limit: int, market: str | None = None) -> RuleInput:
    return RuleInput(kind=kind, limit_percent=limit, market=market, enabled=True)


def test_saved_rules_replace_the_old_ones_and_are_checked_at_once() -> None:
    # The sample's largest target is TSMC's 25 and its US holdings add up to 20.
    rules = [_rule("max_holding_weight", 20), _rule("max_market_weight", 20, "US")]

    view = asyncio.run(store.save_rules(rules))

    checks = view.rule_checks
    assert [(rule.kind, rule.met) for rule in checks.rules] == [
        ("max_holding_weight", False),
        ("max_market_weight", True),
    ]
    assert checks.rules[0].breaking == ["2330.TW"]
    assert (checks.met, checks.enabled) == (1, 2)
    profile = asyncio.run(store.read_profile())
    assert [rule.limit_percent for rule in profile.rules] == [20, 20]


def test_refused_rules_leave_the_saved_ones_as_they_were() -> None:
    with pytest.raises(store.RuleRefusedError):
        asyncio.run(store.save_rules([_rule("max_holding_weight", 101)]))

    profile = asyncio.run(store.read_profile())
    assert [rule.limit_percent for rule in profile.rules] == [
        rule.limit_percent for rule in SAMPLE.rules
    ]


def _holdings(*symbols: str, cash: str = "600000") -> HoldingsRequest:
    """The sample's holdings named, as the page sends them, then any others."""
    sample = {holding.symbol: holding for holding in SAMPLE.holdings}
    return HoldingsRequest(
        holdings=[
            HoldingInput(
                symbol=symbol,
                names=sample[symbol].names
                if symbol in sample
                else {"zh-TW": "蘋果", "en": "Apple"},
                quantity=sample[symbol].quantity if symbol in sample else Decimal("5"),
                average_cost=sample[symbol].average_cost
                if symbol in sample
                else Decimal("180.25"),
            )
            for symbol in symbols
        ],
        cash=Decimal(cash),
    )


def test_saved_holdings_replace_the_old_ones_and_their_targets_follow() -> None:
    # MSFT (target 8) is removed and AAPL added; the others keep their order and targets.
    _save(cash=30)
    kept = ["2330.TW", "2308.TW", "0050.TW", "006208.TW", "NVDA"]

    view = asyncio.run(store.save_holdings(_holdings(*kept, "AAPL", cash="123456.78")))

    assert [holding.symbol for holding in view.holdings] == [*kept, "AAPL", "CASH"]
    aapl = view.holdings[-2]
    assert (aapl.market, aapl.currency, aapl.average_cost) == (
        "US",
        "USD",
        Decimal("180.25"),
    )
    assert view.holdings[-1].quantity == Decimal("123456.78")
    targets = {row.symbol: row.current for row in view.targets}
    assert targets == {symbol: SAMPLE.targets[symbol] for symbol in kept} | {
        "AAPL": 0,
        "CASH": SAMPLE.targets["CASH"],
    }
    assert view.targets_total == 100 - SAMPLE.targets["MSFT"]
    # The open proposal was checked against the holdings before, so it is closed.
    assert view.proposal is None
    profile = asyncio.run(store.read_profile())
    assert "MSFT" not in profile.symbols


def test_refused_holdings_leave_the_saved_ones_as_they_were() -> None:
    with pytest.raises(store.HoldingRefusedError):
        asyncio.run(store.save_holdings(_holdings("2330.TW", "0700.HK")))

    profile = asyncio.run(store.read_profile())
    assert profile.symbols == [holding.symbol for holding in SAMPLE.holdings]
    assert profile.targets == SAMPLE.targets


def test_a_proposal_shows_each_rule_on_the_current_and_the_proposed_targets() -> None:
    asyncio.run(store.save_rules([_rule("max_holding_weight", 20)]))
    # Cash from 10 to 30, TSMC from 25 to 5.
    _save(cash=30)

    view = asyncio.run(store.read_strategy())

    assert view.proposal is not None
    assert view.rule_checks.rules[0].met is False
    assert view.proposal.rule_checks.rules[0].met is True
    assert view.proposal.rule_checks.rules[0].measured == 20


def test_the_view_values_the_sample_read_from_the_database_at_given_prices() -> None:
    at = datetime(2026, 11, 24, 1, 30, tzinfo=UTC)
    prices = {
        "2330.TW": "1500",
        "2308.TW": "1200",
        "0050.TW": "60",
        "006208.TW": "120",
        "NVDA": "180",
        "TWD=X": "32",
    }

    async def view() -> StrategyView:
        state = StrategyState()
        await state.start(None, [])
        for symbol, price in prices.items():
            state.price(Quote(symbol, Decimal(price), None, "live", at))
        try:
            return await state.view()
        finally:
            await state.stop()

    result = asyncio.run(view())

    valuation = result.valuation
    assert [row.symbol for row in valuation.holdings] == [
        h.symbol for h in SAMPLE.holdings
    ]
    # Microsoft has no price, so it is left out; NVIDIA is 150 x 180 x 32.
    assert valuation.left_out == ["MSFT"]
    assert valuation.total_value == Decimal("8064000.00")
    assert valuation.holdings[0].weight == Decimal("37.20")
    assert valuation.holdings[4].value == Decimal("864000.00")
    assert {row.symbol: row.current for row in result.targets} == SAMPLE.targets
