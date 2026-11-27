"""A question that asks to revise the strategy, answered by stand-in programs: no model starts and
no database is read."""

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest

from chat_bridge.chat import claude_code, service
from chat_bridge.chat.claude_code import Login, LoginStatus
from chat_bridge.chat.programs import Effort, Program
from chat_bridge.chat.schemas import ChatDelta, Source
from chat_bridge.chat.split import SplitOutcome
from chat_bridge.strategy import store
from chat_bridge.strategy.compute import valuation
from chat_bridge.strategy.history import History
from chat_bridge.strategy.prices import PriceBook, Quote, latest_quote
from chat_bridge.strategy.proposal import PROPOSAL_SCHEMA, CheckedProposal
from chat_bridge.strategy.revision import RevisionReplyError
from chat_bridge.strategy.schemas import (
    HoldingView,
    ProposalView,
    RuleChecks,
    RuleView,
)
from chat_bridge.strategy.state import STATE
from tests.strategy.test_valuation import HOLDINGS, NOW, US_DAY

QUESTION = "依據聯準會這半年的動向，調整我的配置以降低風險"
SECTION = service.FoundSection(
    section_id=7,
    source=Source(
        number=1,
        file="data/truth/2026-09-16-fomc-raises-rate.md",
        title="聯準會9月升息",
        heading="事件發生",
        event_date=date(2026, 9, 16),
    ),
    text="section text",
    score=0.03,
)
PROFILE = store.Profile(
    holdings=[
        HoldingView(
            symbol=symbol,
            names={"zh-TW": symbol, "en": symbol},
            market=market,
            currency="TWD",
            quantity=Decimal(10),
            average_cost=Decimal(1),
        )
        for symbol, market in (("2330.TW", "TW"), ("NVDA", "US"), ("CASH", None))
    ],
    targets={"2330.TW": 50, "NVDA": 30, "CASH": 20},
    rules=[
        RuleView(kind="max_holding_weight", limit_percent=60, market=None, enabled=True)
    ],
)
ANSWER = "聯準會在 2026-09-16 升息 [1]，建議提高現金。"
GOOD_PROPOSAL: dict[str, Any] = {
    "targets": [
        {"symbol": "2330.TW", "percent": 45},
        {"symbol": "NVDA", "percent": 25},
        {"symbol": "CASH", "percent": 30},
    ],
    "reasons": [{"text": "升息提高風險", "sources": [1]}],
}
COMMAND = ["claude", "-p", "--json-schema", "{}"]


class Run:
    """What the stand-ins saw: the program's input and schema, the record, the saved proposal."""

    def __init__(self) -> None:
        self.inputs: list[str] = []
        self.schemas: list[dict[str, Any]] = []
        # The level each shaped run was started at.
        self.efforts: list[object] = []
        # The level the split was asked at.
        self.split_effort: object = None
        self.records: list[dict[str, Any]] = []
        self.saved: list[CheckedProposal] = []
        self.streamed = False
        # The input of an answer that streams, a question that asks for no revision.
        self.streamed_input = ""
        self.profile_read = False
        # What the split was given of the holdings.
        self.split_holdings: object = None


@pytest.fixture
def run(monkeypatch: pytest.MonkeyPatch) -> Run:
    seen = Run()

    async def revise(
        program: object,
        question: str,
        holdings: object = None,
        *,
        effort: object = None,
    ) -> SplitOutcome:
        seen.split_holdings = holdings
        seen.split_effort = effort
        return SplitOutcome(revise=True)

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def profile() -> store.Profile:
        seen.profile_read = True
        return PROFILE

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        seen.records.append({"question": question, "answer": answer, **kwargs})

    async def save(
        question: str, program: Program, checked: CheckedProposal, sources: list[Source]
    ) -> ProposalView:
        seen.saved.append(checked)
        return ProposalView(
            id=5,
            created_at=datetime(2026, 11, 24, tzinfo=UTC),
            question=question,
            program=program,
            status="open",
            rows=[],
            rule_checks=RuleChecks(met=0, enabled=0, rules=[]),
            reasons=checked.reasons,
            sources=sources,
        )

    async def streamed(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
        effort: object = None,
    ) -> AsyncIterator[str]:
        seen.streamed = True
        seen.streamed_input = input_text
        yield "一般答案"

    monkeypatch.setattr(service, "split_question", revise)
    monkeypatch.setattr(service, "_record", record)
    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", streamed)
    monkeypatch.setattr(store, "read_profile", profile)
    monkeypatch.setattr(store, "save_proposal", save)
    return seen


def _reply_with(seen: Run, monkeypatch: pytest.MonkeyPatch, reply: Any) -> None:
    async def shaped(
        system_prompt: str,
        input_text: str,
        schema: dict[str, Any],
        *,
        on_start: Callable[[list[str]], None],
        effort: object = None,
    ) -> dict[str, Any]:
        on_start(COMMAND)
        seen.inputs.append(input_text)
        seen.schemas.append(schema)
        seen.efforts.append(effort)
        return reply  # type: ignore[no-any-return]

    monkeypatch.setattr(claude_code, "reply_in_shape", shaped)


def _read() -> list[ChatDelta]:
    async def collect() -> list[ChatDelta]:
        return [delta async for delta in service.answer_stream(QUESTION, [SECTION])]

    return asyncio.run(collect())


def test_the_split_is_given_the_holdings_but_cash_before_the_search(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": None})

    _read()

    # The profile's names are its symbols here; each holding is named once.
    assert run.split_holdings == ["2330.TW: 2330.TW", "NVDA: NVDA"]


def test_a_revision_question_is_split_and_answered_at_its_level(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": None})

    async def collect() -> None:
        async for _ in service.answer_stream(QUESTION, [SECTION], effort=Effort.HIGH):
            pass

    asyncio.run(collect())

    assert run.split_effort is Effort.HIGH
    assert run.efforts == [Effort.HIGH]


def test_a_revision_answer_comes_whole_then_the_checked_proposal(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": GOOD_PROPOSAL})

    context, text, proposal = _read()

    assert context.context is not None
    assert context.context.proposal_expected
    assert text.delta == ANSWER
    assert proposal.type == "response.proposal"
    assert proposal.proposal is not None
    assert proposal.proposal.proposal is not None
    assert proposal.proposal.proposal.id == 5
    assert proposal.proposal.refused is None
    [saved] = run.saved
    assert saved.targets == {"2330.TW": 45, "NVDA": 25, "CASH": 30}
    assert not run.streamed


def test_the_program_gets_the_profile_as_data_between_the_sources_and_the_question(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": None})

    _read()

    [sent] = run.inputs
    assert (
        sent.index("</sources>") < sent.index("<strategy>") < sent.index("<question>")
    )
    assert '"symbol": "NVDA"' in sent
    assert '"target_percent": 30' in sent
    assert '"kind": "max_holding_weight"' in sent
    assert run.schemas == [PROPOSAL_SCHEMA]


def test_the_program_gets_the_latest_prices_with_their_time_and_none_for_a_missing_one(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": None})
    book = PriceBook()
    book.put(Quote("NVDA", Decimal("180.5"), Decimal("175"), "daily", US_DAY))
    book.put(Quote("TWD=X", Decimal("32.1"), None, "live", NOW))
    monkeypatch.setattr(STATE, "book", book)

    _read()

    [sent] = run.inputs
    data = json.loads(sent[sent.index("<strategy>") + 10 : sent.index("</strategy>")])
    prices = {
        holding["symbol"]: holding["latest_price"] for holding in data["holdings"]
    }
    assert prices["NVDA"] == {
        "price": "180.5",
        "previous_close": "175",
        "basis": "daily",
        "time": None,
        "day": "2026-11-21",
    }
    assert prices["2330.TW"] is None
    assert data["exchange_rates_to_TWD"]["USD"]["price"] == "32.1"


def test_the_program_gets_the_previous_close_the_panel_measures_from(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": None})
    book = PriceBook()
    # The days as FinMind gave them, then a live price that does not say its previous close.
    days = History(
        read_on=date(2026, 11, 25),
        closes={
            date(2026, 11, 24): Decimal("2230"),
            date(2026, 11, 25): Decimal("2150"),
        },
    )
    book.put(latest_quote("2330.TW", days) or pytest.fail("no daily value"))
    book.put(
        Quote(
            "2330.TW",
            Decimal("2155"),
            None,
            "live",
            datetime(2026, 11, 25, 5, tzinfo=UTC),
        )
    )
    monkeypatch.setattr(STATE, "book", book)

    _read()

    [sent] = run.inputs
    data = json.loads(sent[sent.index("<strategy>") + 10 : sent.index("</strategy>")])
    [given] = [
        holding["latest_price"]
        for holding in data["holdings"]
        if holding["symbol"] == "2330.TW"
    ]
    assert (given["price"], given["previous_close"]) == ("2155", "2230")
    [panel] = [
        quote for quote in valuation(HOLDINGS, book).quotes if quote.symbol == "2330.TW"
    ]
    assert panel.change_percent == Decimal("-3.36")


def test_the_record_keeps_the_answer_the_command_line_and_the_proposal(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": GOOD_PROPOSAL})

    _read()

    [written] = run.records
    assert written["answer"] == ANSWER
    assert written["command_line"] == COMMAND
    assert written["error"] is None
    assert written["proposal"]["proposal"]["id"] == 5


def test_a_proposal_that_fails_a_check_is_refused_with_its_reason_and_not_kept(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    not_100 = {
        **GOOD_PROPOSAL,
        "targets": [*GOOD_PROPOSAL["targets"][:2], {"symbol": "CASH", "percent": 10}],
    }
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": not_100})

    _, text, proposal = _read()

    assert text.delta == ANSWER
    assert proposal.proposal is not None
    assert proposal.proposal.proposal is None
    assert proposal.proposal.refused is not None
    assert proposal.proposal.refused.code == "not_100"
    assert run.saved == []
    assert run.records[0]["proposal"]["refused"]["code"] == "not_100"


def test_a_proposal_not_in_its_shape_still_shows_the_answer_and_says_why_it_was_refused(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A real run once added a reason without a source, which cost the whole answer.
    unsourced = {
        **GOOD_PROPOSAL,
        "reasons": [*GOOD_PROPOSAL["reasons"], {"text": "另一個理由", "sources": []}],
    }
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": unsourced})

    _, text, proposal = _read()

    assert text.delta == ANSWER
    assert proposal.proposal is not None
    assert proposal.proposal.proposal is None
    assert proposal.proposal.refused is not None
    assert proposal.proposal.refused.code == "not_the_shape"
    assert run.saved == []
    assert run.records[0]["answer"] == ANSWER
    assert run.records[0]["error"] is None
    assert run.records[0]["proposal"]["refused"]["code"] == "not_the_shape"


def test_no_proposal_is_said_as_neither_a_proposal_nor_a_refusal(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"answer": "資料不足以修正。", "proposal": None})

    _, _, proposal = _read()

    assert proposal.proposal is not None
    assert proposal.proposal.proposal is None
    assert proposal.proposal.refused is None
    assert run.saved == []


def test_the_current_targets_handed_back_are_said_as_no_proposal_and_not_kept(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The current targets in another order: still nothing for the person to decide.
    same = {
        **GOOD_PROPOSAL,
        "targets": [
            {"symbol": symbol, "percent": percent}
            for symbol, percent in reversed(PROFILE.targets.items())
        ],
    }
    _reply_with(run, monkeypatch, {"answer": "不需要調整。[1]", "proposal": same})

    _, text, proposal = _read()

    assert text.delta == "不需要調整。[1]"
    assert proposal.proposal is not None
    assert proposal.proposal.proposal is None
    assert proposal.proposal.refused is None
    assert run.saved == []
    assert run.records[0]["proposal"] == {"proposal": None, "refused": None}


def test_a_reply_that_is_not_the_shape_fails_after_the_context_and_is_recorded(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    _reply_with(run, monkeypatch, {"text": "no answer field"})
    read: list[ChatDelta] = []

    async def collect() -> None:
        async for delta in service.answer_stream(QUESTION, [SECTION]):
            read.append(delta)

    with pytest.raises(RevisionReplyError):
        asyncio.run(collect())

    assert [delta.type for delta in read] == ["response.context"]
    assert "not an answer and a proposal" in run.records[0]["error"]
    assert run.saved == []


def test_a_question_that_asks_for_no_revision_streams_with_the_holdings_and_no_proposal(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_revision(
        program: object,
        question: str,
        holdings: object = None,
        *,
        effort: object = None,
    ) -> SplitOutcome:
        return SplitOutcome()

    monkeypatch.setattr(service, "split_question", no_revision)
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": GOOD_PROPOSAL})

    deltas = _read()

    assert [delta.type for delta in deltas] == [
        "response.context",
        "response.output_text.delta",
    ]
    assert deltas[0].context is not None
    assert not deltas[0].context.proposal_expected
    assert run.streamed
    assert run.inputs == []
    # Advice depends on what the person holds now, so the plain answer is given the holdings,
    # with the numbers the service computed, before the question.
    assert run.profile_read
    sent = run.streamed_input
    assert sent.index("<strategy>") < sent.index("<question>")
    assert '"value_TWD"' in sent
    assert '"weight_percent"' in sent


def test_without_a_profile_a_revision_question_is_answered_as_any_other(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def missing() -> store.Profile:
        raise store.ProfileMissingError()

    monkeypatch.setattr(store, "read_profile", missing)
    _reply_with(run, monkeypatch, {"answer": ANSWER, "proposal": GOOD_PROPOSAL})

    deltas = _read()

    assert deltas[0].context is not None
    assert not deltas[0].context.proposal_expected
    assert run.streamed
    assert [delta.type for delta in deltas][-1] == "response.output_text.delta"
