"""A table or note an earlier source already holds is sent to the model once (spec 020), and the
page's sources and the record's sections stay as they were; without starting a model."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from chat_bridge.chat import claude_code, service
from chat_bridge.chat.programs import Login, LoginStatus
from chat_bridge.chat.schemas import ChatDelta, Source
from chat_bridge.chat.split import SplitOutcome

NOTE = "> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US。"
TABLE = (
    "| 序列 | D0 | 當日% |\n"
    "|---|---|---|\n"
    "| 元大台灣50 0050 | 2026-11-06 | -4.79% |\n"
    "| 富邦台50 006208 | 2026-11-06 | -5.59% |"
)


def _section(
    number: int, text: str, heading: str = "當日與之後的行情"
) -> service.FoundSection:
    return service.FoundSection(
        section_id=100 + number,
        source=Source(
            number=number,
            file=f"{number}.md",
            title="T",
            heading=heading,
            event_date=None,
        ),
        text=text,
        score=0.03,
    )


def _market(number: int, own_note: str, table: str = TABLE) -> service.FoundSection:
    return _section(number, f"{NOTE}\n\n{table}\n\n> {own_note}")


def _sources_of(sent: str) -> dict[int, str]:
    """Each source's text in the model's input, by its number."""
    sources = sent.split("<sources>\n", 1)[1].split("\n</sources>", 1)[0]
    texts = {}
    for block in sources.split("\n\n["):
        header, _, text = block.lstrip("[").partition("\n")
        texts[int(header.split("]", 1)[0])] = text
    return texts


def test_a_table_an_earlier_source_holds_is_sent_once_with_a_pointer() -> None:
    sent = service.model_input("q", [_market(3, "第一則"), _market(9, "第二則")])

    texts = _sources_of(sent)
    assert TABLE in texts[3]
    assert TABLE not in texts[9]
    assert "(same table as [3])" in texts[9]
    assert "> 第二則" in texts[9]
    assert sent.count("| 元大台灣50 0050 |") == 1


def test_a_note_an_earlier_source_holds_gets_its_pointer() -> None:
    texts = _sources_of(service.model_input("q", [_market(3, "a"), _market(9, "b")]))

    assert NOTE in texts[3]
    assert texts[9].startswith("(same note as [3])\n")


def test_tables_that_differ_in_one_character_are_both_sent_whole() -> None:
    other = TABLE.replace("-4.79%", "-4.78%")

    texts = _sources_of(
        service.model_input("q", [_market(3, "a"), _market(9, "b", other)])
    )

    assert TABLE in texts[3]
    assert other in texts[9]


def test_a_source_with_nothing_sent_before_is_sent_as_it_is() -> None:
    news = _section(1, "聯準會宣布升息一碼。\n\n> 引述的一句話。", heading="事件發生")

    assert _sources_of(service.model_input("q", [news]))[1] == news.text


@pytest.mark.parametrize(
    "repeated",
    [
        pytest.param(">", id="a lone quote mark"),
        pytest.param("> 短", id="a short note"),
        pytest.param("| a |", id="a short table"),
    ],
)
def test_what_is_not_longer_than_its_pointer_is_sent_as_it_is(repeated: str) -> None:
    first = _section(3, f"甲\n{repeated}\n乙")
    second = _section(9, f"丙\n{repeated}\n丁")

    texts = _sources_of(service.model_input("q", [first, second]))

    assert texts[9] == second.text


def test_a_repeat_inside_one_source_is_sent_there_and_later_ones_point_at_that_source() -> (
    None
):
    twice = _section(4, f"{TABLE}\n\n{TABLE}")
    later = _section(5, TABLE)

    texts = _sources_of(service.model_input("q", [twice, later]))

    assert texts[4] == twice.text
    assert "(same table as [4])" not in texts[4]
    assert texts[5] == "(same table as [4])"


def test_every_distinct_table_row_is_in_the_input() -> None:
    other = TABLE.replace("2026-11-06", "2026-11-09")
    sections = [
        _market(1, "a"),
        _market(2, "b"),
        _market(3, "c", other),
        _market(4, "d"),
    ]

    sent = service.model_input("q", sections)

    rows = {
        line for s in sections for line in s.text.split("\n") if line.startswith("|")
    }
    assert all(row in sent for row in rows)


def test_the_page_and_the_record_keep_every_source_and_the_record_keeps_what_was_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sections = [_market(1, "a"), _market(2, "b")]
    given: list[str] = []
    records: list[dict[str, Any]] = []

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def split_question(
        program: object,
        question: str,
        holdings: object = None,
        *,
        effort: object = None,
    ) -> SplitOutcome:
        return SplitOutcome()

    async def answer(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Any,
        effort: object = None,
        on_usage: Any = None,
    ) -> AsyncIterator[str]:
        given.append(input_text)
        on_start(["claude"])
        yield "ok"

    async def record(
        question: str, answer: str, kept: list[service.FoundSection], **kwargs: Any
    ) -> None:
        records.append({"sections": kept, **kwargs})

    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", answer)
    monkeypatch.setattr(service, "split_question", split_question)
    monkeypatch.setattr(service, "_record", record)

    async def run() -> list[ChatDelta]:
        return [delta async for delta in service.answer_stream("q", sections)]

    deltas = asyncio.run(run())

    [context] = [delta.context for delta in deltas if delta.type == "response.context"]
    assert context is not None
    assert context.sources == [section.source for section in sections]
    [kept] = records
    assert kept["sections"] == sections
    assert kept["sent_to_model"] == given[0]
    assert "(same table as [1])" in given[0]
