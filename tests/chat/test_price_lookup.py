"""The prices a question's split names: looked up while the parts are searched, given to the program
in `<prices>`, shown to the page and kept in the record; without starting a program or reading a
market data source."""

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from chat_bridge.chat import claude_code, service, split
from chat_bridge.chat.claude_code import Login, LoginStatus
from chat_bridge.chat.schemas import ChatDelta, Source
from chat_bridge.price_history.closes import ClosesError, SeriesCloses
from chat_bridge.price_history.lookups import Lookup
from chat_bridge.price_history.markets import MarketSeries
from chat_bridge.price_history.reading import Reads, SymbolRead

READ_AT = datetime(2026, 11, 28, 10, 0, tzinfo=ZoneInfo("Asia/Taipei"))
SESSIONS = [date(2026, 9, day) for day in (15, 16, 17, 18, 21, 22)]
CLOSES = dict(zip(SESSIONS, [120.0, 121.0, 118.0, 119.0, 122.0, 123.0], strict=True))


def _section(number: int, file: str = "2026-09-16-fomc-raises-rate.md") -> Any:
    return service.FoundSection(
        section_id=100 + number,
        source=Source(
            number=number,
            file=file,
            title="T",
            heading="事件發生",
            event_date=date(2026, 9, 16),
        ),
        text=f"section {number}",
        score=0.03,
        markets=("US",),
    )


def _lookup(symbol: str, start: str, end: str) -> split.PriceRequest:
    return split.PriceRequest(symbol=symbol, start_date=start, end_date=end)


@pytest.fixture
def asked(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Claude Code logged in and answering "ok"; the closes stand in for every symbol; what the
    program, the page and the record got."""
    seen: dict[str, Any] = {"records": [], "reads": []}

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def answer(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
        effort: object = None,
        on_usage: object = None,
    ) -> AsyncIterator[str]:
        seen["input_text"] = input_text
        on_start(["claude"])
        yield "ok"

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        seen["records"].append(kwargs)

    def read_for(lookups: list[Lookup], listed: MarketSeries, now: datetime) -> Reads:
        seen["reads"].append([lookup.series.symbol for lookup in lookups])
        by_symbol = {
            lookup.series.symbol: SymbolRead(
                lookup.series,
                None if lookup.series.symbol == "NVDA" else SeriesCloses(dict(CLOSES)),
                ClosesError("Yahoo NVDA: timed out")
                if lookup.series.symbol == "NVDA"
                else None,
                False,
                READ_AT,
            )
            for lookup in lookups
        }
        return Reads(by_symbol, {"TW": SESSIONS, "US": SESSIONS})

    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", answer)
    monkeypatch.setattr(service, "_record", record)
    monkeypatch.setattr(service, "read_for", read_for)
    return seen


def _ask(
    monkeypatch: pytest.MonkeyPatch,
    outcome: split.SplitOutcome,
    question: str = "聯準會 9 月升息後 006208 怎麼走？",
    sections: list[Any] | None = None,
) -> list[ChatDelta]:
    async def split_question(
        program: object, question: str, holdings: object = None, **options: object
    ) -> split.SplitOutcome:
        return outcome

    monkeypatch.setattr(service, "split_question", split_question)
    found = [_section(1)] if sections is None else sections

    async def run() -> list[ChatDelta]:
        return [delta async for delta in service.answer_stream(question, found)]

    return asyncio.run(run())


def test_the_prices_go_to_the_program_between_the_sources_and_the_question(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    looked_up = split.SplitOutcome(
        prices=[_lookup("006208.TW", "2026-09-15", "2026-09-22")]
    )

    deltas = _ask(monkeypatch, looked_up)

    sent = asked["input_text"]
    assert sent.index("</sources>") < sent.index("<prices>") < sent.index("<question>")
    assert "- 006208.TW (富邦台50 006208), 2026-09-15 to 2026-09-22: first" in sent
    assert "2026-09-16-fomc-raises-rate.md, event date 2026-09-16, sources [1]:" in sent
    assert asked["reads"] == [["006208.TW"]]
    context = deltas[0].context
    assert context is not None and context.prices is not None
    assert [one.symbol for one in context.prices.lookups] == ["006208.TW"]
    assert [event.source_numbers for event in context.prices.events] == [[1]]


def test_the_record_keeps_what_was_asked_left_out_and_given(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    looked_up = split.SplitOutcome(
        prices=[
            _lookup("006208.TW", "2026-09-15", "2026-09-22"),
            _lookup("CASH", "2026-09-15", "2026-09-22"),
            _lookup("7203.T", "2026-09-15", "2026-09-22"),
        ]
    )

    _ask(monkeypatch, looked_up)

    [written] = asked["records"]
    prices = written["prices"]
    assert [one["symbol"] for one in prices["asked"]] == ["006208.TW", "CASH", "7203.T"]
    assert [(one["symbol"], one["reason"]) for one in prices["left_out"]] == [
        ("CASH", "cash"),
        ("7203.T", "unknown_symbol"),
    ]
    [given] = prices["given"]["lookups"]
    assert (given["symbol"], given["stored"]) == ("006208.TW", False)
    sent = asked["input_text"]
    block = sent[sent.index("<prices>") : sent.index("</prices>") + len("</prices>")]
    assert prices["block_characters"] == len(block)
    assert (
        "7203.T 2026-09-15 to 2026-09-22 (a symbol of no market the app reads)" in block
    )


def test_a_symbol_not_read_is_said_to_the_program_and_the_page(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    looked_up = split.SplitOutcome(prices=[_lookup("NVDA", "2026-09-15", "2026-09-22")])

    deltas = _ask(monkeypatch, looked_up)

    sent = asked["input_text"]
    assert (
        "- NVDA, 2026-09-15 to 2026-09-22: not read: Yahoo Finance could not be read"
        in sent
    )
    assert "timed out" not in sent
    context = deltas[0].context
    assert context is not None and context.prices is not None
    not_read = context.prices.lookups[0].not_read
    assert not_read is not None and (not_read.source, not_read.reason) == (
        "yahoo",
        "unreadable",
    )
    [written] = asked["records"]
    assert written["prices"]["read_errors"] == {"NVDA": "Yahoo NVDA: timed out"}


def test_a_failed_split_says_no_prices_were_looked_up(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    deltas = _ask(monkeypatch, split.SplitOutcome(error="the split did not finish"))

    assert "No prices were looked up for this question" in asked["input_text"]
    assert asked["reads"] == []
    context = deltas[0].context
    assert context is not None
    assert (context.split_failed, context.prices) == (True, None)


def test_a_question_about_no_market_has_no_prices(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    deltas = _ask(monkeypatch, split.SplitOutcome())

    assert "<prices>" not in asked["input_text"]
    assert asked["reads"] == []
    context = deltas[0].context
    assert context is not None and context.prices is None


def test_a_question_about_prices_alone_is_answered_from_the_prices(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    looked_up = split.SplitOutcome(
        prices=[_lookup("006208.TW", "2026-09-17", "2026-09-17")]
    )

    deltas = _ask(monkeypatch, looked_up, "006208 在 9 月 17 日的漲跌", sections=[])

    assert deltas[-1].type == "response.completed"
    sent = asked["input_text"]
    assert "<sources>\n\n</sources>" in sent
    assert "| 006208.TW | 2026-09-17 | 118.00 | -2.48% |" in sent


def test_a_question_about_prices_alone_that_looks_nothing_up_gets_the_fixed_line(
    monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any]
) -> None:
    deltas = _ask(
        monkeypatch, split.SplitOutcome(), "006208 在 9 月 17 日的漲跌", sections=[]
    )

    assert deltas[-1].delta == service.NOT_IN_DATA["zh-TW"]
    assert "input_text" not in asked
