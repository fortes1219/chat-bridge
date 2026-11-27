"""Every question is recorded however its answer ends, without starting Claude Code."""

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import date
from typing import Any

import pytest

from chat_bridge.chat import claude_code, service
from chat_bridge.chat.claude_code import Login, LoginStatus
from chat_bridge.chat.schemas import ChatDelta, Source

SECTION = service.FoundSection(
    section_id=7,
    source=Source(
        number=1,
        file="data/truth/a.md",
        title="T",
        heading="H",
        event_date=date(2026, 9, 17),
    ),
    text="section text",
    score=0.03,
)
COMMAND = ["claude", "-p", "--tools", ""]


@pytest.fixture
def records(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """What _record was asked to write, with Claude Code logged in and answering in two pieces."""
    written: list[dict[str, Any]] = []

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        written.append({"question": question, "answer": answer, **kwargs})

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def two_pieces(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
        effort: object = None,
        on_usage: object = None,
    ) -> AsyncIterator[str]:
        on_start(COMMAND)
        yield "聯準會"
        yield "降息。"

    monkeypatch.setattr(service, "_record", record)
    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", two_pieces)
    return written


def _read(count: int | None) -> list[ChatDelta]:
    """Read the stream to its end, or stop after `count` lines as a client that went away."""

    async def run() -> list[ChatDelta]:
        stream = service.answer_stream("q", [SECTION])
        read: list[ChatDelta] = []
        async for delta in stream:
            read.append(delta)
            if count is not None and len(read) == count:
                await stream.aclose()
                break
        return read

    return asyncio.run(run())


def test_an_answered_question_is_recorded_with_its_command_line(
    records: list[dict[str, Any]],
) -> None:
    _read(None)

    [written] = records
    assert written["answer"] == "聯準會降息。"
    assert written["command_line"] == COMMAND
    assert written["sent_to_model"] is not None
    assert written["error"] is None


def test_a_question_whose_client_went_away_is_still_recorded(
    records: list[dict[str, Any]],
) -> None:
    _read(2)  # the context and the first piece

    [written] = records
    assert written["answer"] == "聯準會"
    assert written["error"] == service.CUT_OFF


def test_an_answer_cancelled_at_shutdown_is_recorded_before_the_service_goes_on(
    records: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    # As when uvicorn's shutdown limit passes: the request is cancelled while the program is
    # still writing, and the service goes on to stop the database. It waits for the answer
    # first, so the cut-off answer's record, which takes a moment to write, is written.
    async def slow_record(
        question: str, answer: str, sections: Any, **kwargs: Any
    ) -> None:
        await asyncio.sleep(0.05)
        records.append({"question": question, "answer": answer, **kwargs})

    async def endless(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
        effort: object = None,
        on_usage: object = None,
    ) -> AsyncIterator[str]:
        on_start(COMMAND)
        yield "聯準會"
        await asyncio.Event().wait()
        yield "never sent"

    monkeypatch.setattr(service, "_record", slow_record)
    monkeypatch.setattr(claude_code, "stream_answer", endless)

    async def main() -> list[dict[str, Any]]:
        async def read() -> None:
            async for _ in service.answer_stream("q", [SECTION]):
                pass

        answering = asyncio.create_task(read())
        await asyncio.sleep(0.05)
        answering.cancel()
        await service.finish_answers(1)
        # What the database holds when it is stopped, right after.
        return list(records)

    [written] = asyncio.run(main())
    assert written["answer"] == "聯準會"
    assert written["error"] == service.CUT_OFF
