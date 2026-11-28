"""The tokens a question used (spec 019): each program's own count, never guessed, added up over
the question's runs and sent after an answer that ended, without starting a model."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, cast

import pytest

from chat_bridge.chat import claude_code, codex, service
from chat_bridge.chat.programs import Login, LoginStatus, ProgramError, Usage
from chat_bridge.chat.schemas import ChatDelta, Source
from chat_bridge.chat.split import SplitOutcome

SECTION = service.FoundSection(
    section_id=7,
    source=Source(
        number=1, file="data/truth/a.md", title="T", heading="H", event_date=None
    ),
    text="section text",
    score=0.03,
)
# The same four numbers as each program names them: 100 input, 40 of it read from the cache and
# 60 written to it, 10 output.
CLAUDE_COUNTS = {
    "inputTokens": 100,
    "cacheReadInputTokens": 40,
    "cacheCreationInputTokens": 60,
    "outputTokens": 10,
}
CODEX_COUNTS = {
    "input_tokens": 100,
    "cached_input_tokens": 40,
    "cache_write_input_tokens": 60,
    "output_tokens": 10,
    "reasoning_output_tokens": 5,
}


def _claude_result(**models: dict[str, Any]) -> dict[str, Any]:
    return {"type": "result", "is_error": False, "result": "ok", "modelUsage": models}


def _codex_lines(usage: object) -> list[bytes]:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}},
        {"type": "turn.completed", "usage": usage},
    ]
    return [json.dumps(event).encode() for event in events]


def test_the_same_numbers_add_the_cache_for_claude_code_and_not_for_codex() -> None:
    # Claude Code's input count leaves the cache out; Codex's already holds it.
    assert claude_code.usage_of(_claude_result(opus=CLAUDE_COUNTS)) == Usage(
        input_tokens=200, cached_input_tokens=40, output_tokens=10
    )
    assert codex.usage_of(_codex_lines(CODEX_COUNTS)) == Usage(
        input_tokens=100, cached_input_tokens=40, output_tokens=10
    )


def test_claude_codes_count_adds_up_every_model_of_the_run() -> None:
    small = {
        "inputTokens": 5,
        "cacheReadInputTokens": 0,
        "cacheCreationInputTokens": 0,
        "outputTokens": 2,
    }

    usage = claude_code.usage_of(_claude_result(opus=CLAUDE_COUNTS, haiku=small))

    assert usage == Usage(input_tokens=205, cached_input_tokens=40, output_tokens=12)


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(None, id="no result"),
        pytest.param({"type": "result"}, id="no modelUsage"),
        pytest.param(_claude_result(), id="no model"),
        pytest.param(
            _claude_result(opus={**CLAUDE_COUNTS, "outputTokens": "10"}), id="text"
        ),
        pytest.param(
            _claude_result(opus={**CLAUDE_COUNTS, "inputTokens": -1}), id="negative"
        ),
        pytest.param(
            _claude_result(opus={**CLAUDE_COUNTS, "outputTokens": True}), id="boolean"
        ),
        pytest.param(
            _claude_result(opus={"inputTokens": 1, "outputTokens": 1}), id="missing"
        ),
    ],
)
def test_a_claude_code_count_that_is_not_whole_is_unreported(
    result: dict[str, Any] | None,
) -> None:
    assert claude_code.usage_of(result) is None


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param([], id="no event"),
        pytest.param(_codex_lines(None), id="no usage"),
        pytest.param(_codex_lines({**CODEX_COUNTS, "output_tokens": 1.5}), id="float"),
        pytest.param(
            _codex_lines({"input_tokens": 1, "output_tokens": 1}), id="missing"
        ),
    ],
)
def test_a_codex_count_that_is_not_whole_is_unreported(lines: list[bytes]) -> None:
    assert codex.usage_of(lines) is None


class _Input:
    def write(self, data: bytes) -> None:
        self.data = data

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        return None


class _Finished:
    """Stands in for a finished program that printed the given lines and exited."""

    def __init__(self, lines: list[bytes], exit_code: int) -> None:
        self.stdin = _Input()
        self.stdout = asyncio.StreamReader()
        self.stdout.feed_data(b"".join(line + b"\n" for line in lines))
        self.stdout.feed_eof()
        self.stderr = asyncio.StreamReader()
        self.stderr.feed_eof()
        self.returncode = exit_code

    async def wait(self) -> int:
        return self.returncode


def test_each_program_hands_over_its_runs_tokens_even_when_the_run_failed() -> None:
    reported: list[Usage] = []
    failed = {**_claude_result(opus=CLAUDE_COUNTS), "is_error": True}

    async def run() -> None:
        claude = cast(Any, _Finished([json.dumps(failed).encode()], exit_code=1))
        with pytest.raises(ProgramError):
            async for _ in claude_code._read_answer(claude, "input", reported.append):
                pass
        program = cast(Any, _Finished(_codex_lines(CODEX_COUNTS), exit_code=0))
        await codex._read_answer(program, "input", reported.append)

    asyncio.run(run())

    assert reported == [
        Usage(input_tokens=200, cached_input_tokens=40, output_tokens=10),
        Usage(input_tokens=100, cached_input_tokens=40, output_tokens=10),
    ]


def test_the_questions_total_adds_the_runs_that_reported_and_counts_the_rest() -> None:
    total = service.question_usage(
        [
            ("split", Usage(1_000, 800, 50)),
            ("answer", Usage(90_000, 60_000, 2_000)),
            ("answer", None),
        ]
    )

    assert total.model_dump() == {
        "input_tokens": 91_000,
        "cached_input_tokens": 60_800,
        "output_tokens": 2_050,
        "total_tokens": 93_050,
        "unreported_runs": 1,
    }


def _answering(
    monkeypatch: pytest.MonkeyPatch,
    split: SplitOutcome,
    answer_usage: Usage | None,
    fails: bool = False,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def split_question(
        program: object,
        question: str,
        holdings: object = None,
        *,
        series: object = None,
        effort: object = None,
    ) -> SplitOutcome:
        return split

    async def answer(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Any,
        effort: object = None,
        on_usage: Any = None,
    ) -> AsyncIterator[str]:
        on_start(["claude"])
        yield "ok"
        if answer_usage is not None:
            on_usage(answer_usage)
        if fails:
            raise ProgramError("the program stopped")

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        records.append(kwargs)

    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", answer)
    monkeypatch.setattr(service, "split_question", split_question)
    monkeypatch.setattr(service, "_record", record)
    return records


def _read(sections: list[service.FoundSection]) -> list[ChatDelta]:
    async def run() -> list[ChatDelta]:
        read: list[ChatDelta] = []
        try:
            async for delta in service.answer_stream("q", sections):
                read.append(delta)
        except ProgramError:
            pass
        return read

    return asyncio.run(run())


def test_an_answer_that_ended_is_followed_by_the_split_and_the_answer_added_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = _answering(
        monkeypatch,
        SplitOutcome(usage=Usage(1_000, 800, 50)),
        Usage(90_000, 60_000, 2_000),
    )

    deltas = _read([SECTION])

    assert deltas[-1].type == "response.completed"
    assert deltas[-1].usage is not None
    assert deltas[-1].usage.total_tokens == 93_050
    assert deltas[-1].usage.unreported_runs == 0
    [kept] = records
    assert [run[0] for run in kept["runs"]] == ["split", "answer"]


def test_a_split_that_reported_nothing_is_said_not_counted_as_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _answering(
        monkeypatch,
        SplitOutcome(error="the split did not finish within 120 seconds"),
        Usage(500, 0, 20),
    )

    usage = _read([SECTION])[-1].usage

    assert usage is not None
    assert (usage.total_tokens, usage.unreported_runs) == (520, 1)


def test_a_failed_answer_has_no_total_but_its_runs_are_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = _answering(
        monkeypatch, SplitOutcome(usage=Usage(10, 0, 1)), Usage(500, 0, 20), fails=True
    )

    deltas = _read([SECTION])

    assert "response.completed" not in [delta.type for delta in deltas]
    [kept] = records
    assert kept["error"] == "the program stopped"
    assert kept["runs"] == [("split", Usage(10, 0, 1)), ("answer", Usage(500, 0, 20))]


def test_a_question_the_data_has_nothing_on_runs_no_program_and_has_no_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = _answering(monkeypatch, SplitOutcome(), None)

    deltas = _read([])

    assert [delta.type for delta in deltas] == [
        "response.context",
        "response.output_text.delta",
    ]
    assert records[0]["runs"] == []


def test_the_record_keeps_each_runs_tokens_and_the_total() -> None:
    details = service._usage_details([("split", None), ("answer", Usage(5, 1, 2))])

    assert details == {
        "runs": [
            {"run": "split", "usage": None},
            {
                "run": "answer",
                "usage": {
                    "input_tokens": 5,
                    "cached_input_tokens": 1,
                    "output_tokens": 2,
                },
            },
        ],
        "total": {
            "input_tokens": 5,
            "cached_input_tokens": 1,
            "output_tokens": 2,
            "total_tokens": 7,
            "unreported_runs": 1,
        },
    }
