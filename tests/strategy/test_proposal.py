"""The checks a proposal must pass before it is shown, without a model or a database."""

from typing import Any

import pytest
from pydantic import ValidationError

from chat_bridge.strategy.proposal import (
    PROPOSAL_SCHEMA,
    CheckedProposal,
    ProposalReply,
    check_proposal,
    read_reply,
)
from chat_bridge.strategy.schemas import ProposalRefusal

SYMBOLS = ["2330.TW", "NVDA", "CASH"]
SOURCES = {1, 2, 3}
REASON = {"text": "聯準會升息", "sources": [1]}


def _proposal(
    targets: dict[str, Any], reasons: list[dict[str, Any]] | None = None
) -> ProposalReply:
    return ProposalReply.model_validate(
        {
            "targets": [
                {"symbol": symbol, "percent": percent}
                for symbol, percent in targets.items()
            ],
            "reasons": reasons if reasons is not None else [REASON],
        }
    )


def _refusal(targets: dict[str, Any], **kwargs: Any) -> ProposalRefusal:
    checked = check_proposal(_proposal(targets, **kwargs), SYMBOLS, SOURCES)
    assert isinstance(checked, ProposalRefusal)
    return checked


def test_a_proposal_for_every_holding_adding_up_to_100_passes_in_the_profiles_order() -> (
    None
):
    checked = check_proposal(
        _proposal({"CASH": 20, "2330.TW": 50, "NVDA": 30}), SYMBOLS, SOURCES
    )

    assert isinstance(checked, CheckedProposal)
    assert list(checked.targets) == SYMBOLS
    assert checked.targets == {"2330.TW": 50, "NVDA": 30, "CASH": 20}
    assert checked.reasons[0].sources == [1]


def test_a_holding_not_in_the_profile_is_refused() -> None:
    refusal = _refusal({"2330.TW": 50, "NVDA": 20, "CASH": 20, "TSLA": 10})

    assert refusal.code == "unknown_holding"
    assert "TSLA" in refusal.message


def test_a_holding_listed_twice_is_refused() -> None:
    proposal = ProposalReply.model_validate(
        {
            "targets": [
                {"symbol": "2330.TW", "percent": 50},
                {"symbol": "2330.TW", "percent": 20},
                {"symbol": "NVDA", "percent": 10},
                {"symbol": "CASH", "percent": 20},
            ],
            "reasons": [REASON],
        }
    )

    checked = check_proposal(proposal, SYMBOLS, SOURCES)

    assert isinstance(checked, ProposalRefusal)
    assert checked.code == "repeated_holding"


@pytest.mark.parametrize("percent", [-10, 101])
def test_a_percent_outside_0_to_100_is_refused(percent: int) -> None:
    refusal = _refusal({"2330.TW": percent, "NVDA": 50, "CASH": 60 - percent})

    assert refusal.code == "percent_out_of_range"


def test_a_holding_without_a_target_is_refused() -> None:
    refusal = _refusal({"2330.TW": 70, "NVDA": 30})

    assert refusal.code == "missing_holding"
    assert "CASH" in refusal.message


@pytest.mark.parametrize("cash", [19, 21])
def test_targets_that_do_not_add_up_to_100_are_refused(cash: int) -> None:
    refusal = _refusal({"2330.TW": 50, "NVDA": 30, "CASH": cash})

    assert refusal.code == "not_100"


def test_a_reason_citing_a_source_the_answer_does_not_have_is_refused() -> None:
    refusal = _refusal(
        {"2330.TW": 50, "NVDA": 30, "CASH": 20},
        reasons=[REASON, {"text": "另一個理由", "sources": [2, 9]}],
    )

    assert refusal.code == "unknown_source"
    assert "9" in refusal.message


@pytest.mark.parametrize(
    "reply",
    [
        {},
        {"answer": "a"},
        {"answer": "a", "proposal": None, "note": "extra"},
        {"answer": 1, "proposal": None},
    ],
)
def test_a_reply_with_no_answer_to_show_is_not_read(reply: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        read_reply(reply)


CASH_ONLY = [{"symbol": "CASH", "percent": 100}]


@pytest.mark.parametrize(
    "proposal",
    [
        "move to cash",
        {"targets": [], "reasons": []},
        {"targets": CASH_ONLY, "reasons": [{"text": "r", "sources": []}]},
        {"targets": [{"symbol": "CASH", "percent": 99.5}], "reasons": [REASON]},
        {"targets": [{"symbol": "CASH", "percent": "100"}], "reasons": [REASON]},
        {"targets": CASH_ONLY, "reasons": [{"text": "   ", "sources": [1]}]},
        {"targets": CASH_ONLY, "reasons": [REASON], "note": "extra"},
    ],
)
def test_a_proposal_not_in_its_shape_is_refused_and_the_answer_is_kept(
    proposal: Any,
) -> None:
    read = read_reply({"answer": "回答。[1]", "proposal": proposal})

    assert read.answer == "回答。[1]"
    assert isinstance(read.proposal, ProposalRefusal)
    assert read.proposal.code == "not_the_shape"


def test_a_reply_with_no_proposal_is_read() -> None:
    assert read_reply({"answer": "沒有修正", "proposal": None}).proposal is None


def test_the_schema_asks_for_the_answer_and_the_proposal_and_nothing_else() -> None:
    assert PROPOSAL_SCHEMA["required"] == ["answer", "proposal"]
    assert PROPOSAL_SCHEMA["additionalProperties"] is False
