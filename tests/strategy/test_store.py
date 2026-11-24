"""The profile, its targets and the proposals in the embedded database.

Each test gets a database of its own with the repository's sample profile loaded, so the tests are
marked slow. No program and no embedding model is used.
"""

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest

from chat_bridge.chat.programs import Program
from chat_bridge.chat.sources import Source
from chat_bridge.strategy import store
from chat_bridge.strategy.proposal import CheckedProposal
from chat_bridge.strategy.sample import load_sample_if_empty, read_sample
from chat_bridge.strategy.schemas import Reason
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
