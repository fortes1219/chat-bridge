"""The level a question is answered at: the request takes only three, each run of the question gets
it, and each program starts at it (spec 018), without starting a model."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat import claude_code, codex, service
from chat_bridge.chat.programs import Effort, Login, LoginStatus
from chat_bridge.chat.schemas import ChatDelta, Source
from chat_bridge.chat.server import create_app
from chat_bridge.chat.split import SplitOutcome

SECTION = service.FoundSection(
    section_id=7,
    source=Source(
        number=1, file="data/truth/a.md", title="T", heading="H", event_date=None
    ),
    text="section text",
    score=0.03,
)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """The service, with a search that finds one section and an answer that says which level it
    was asked at."""
    searched: list[str] = []

    async def found(question: str) -> list[service.FoundSection]:
        searched.append(question)
        return [SECTION]

    async def answer(
        question: str, sections: object, program: object, effort: Effort
    ) -> AsyncIterator[ChatDelta]:
        yield ChatDelta(type="response.output_text.delta", delta=effort.value)

    monkeypatch.setattr(service, "find_sections", found)
    monkeypatch.setattr(service, "answer_stream", answer)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        test_client.searched = searched  # type: ignore[attr-defined]
        yield test_client


@pytest.mark.parametrize(
    ("body", "level"),
    [
        pytest.param({"question": "q", "effort": "low"}, "low", id="low"),
        pytest.param({"question": "q", "effort": "high"}, "high", id="high"),
        pytest.param({"question": "q"}, "medium", id="none is medium"),
    ],
)
def test_the_request_level_reaches_the_answer(
    client: TestClient, body: dict[str, str], level: str
) -> None:
    response = client.post("/chat/stream", json=body)

    assert response.status_code == 200
    assert f'"delta":"{level}"' in response.text.replace(" ", "")


@pytest.mark.parametrize("level", ["xhigh", "max", "ultracode", "LOW", ""])
def test_a_level_other_than_the_three_is_refused_before_the_search(
    client: TestClient, level: str
) -> None:
    response = client.post("/chat/stream", json={"question": "q", "effort": level})

    assert response.status_code == 422
    assert client.searched == []  # type: ignore[attr-defined]


def test_the_shell_cannot_set_claude_codes_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_EFFORT_LEVEL", "max")

    assert "CLAUDE_CODE_EFFORT_LEVEL" not in claude_code.child_env()


def _command_lines(
    monkeypatch: pytest.MonkeyPatch, module: Any, effort: Effort | None
) -> tuple[list[str], list[str]]:
    """The command lines of a shaped reply and of an answer at `effort`; neither program starts."""

    async def not_started(args: list[str], *, with_input: bool) -> Any:
        raise OSError("not started")

    monkeypatch.setattr(module, "_start", not_started)
    monkeypatch.setattr(module, "find_executable", lambda: "program")
    shaped: list[str] = []
    streamed: list[str] = []

    async def run() -> None:
        with pytest.raises(OSError):
            await module.reply_in_shape(
                "rules", "input", {}, on_start=shaped.extend, effort=effort
            )
        with pytest.raises(OSError):
            async for _ in module.stream_answer(
                "rules", "input", on_start=streamed.extend, effort=effort
            ):
                pass

    asyncio.run(run())
    return shaped, streamed


@pytest.mark.parametrize("effort", list(Effort))
def test_claude_code_starts_at_the_level(
    monkeypatch: pytest.MonkeyPatch, effort: Effort
) -> None:
    for args in _command_lines(monkeypatch, claude_code, effort):
        at = args.index("--effort")
        assert args[at + 1] == effort.value
        assert args.count("--effort") == 1


@pytest.mark.parametrize("effort", list(Effort))
def test_codex_starts_at_the_level(
    monkeypatch: pytest.MonkeyPatch, effort: Effort
) -> None:
    setting = f"model_reasoning_effort='{effort.value}'"
    for args in _command_lines(monkeypatch, codex, effort):
        at = args.index(setting)
        assert args[at - 1] == "-c"
        # A setting of the program, before the `exec` command.
        assert at < args.index("exec")


@pytest.mark.parametrize("module", [claude_code, codex], ids=["claude-code", "codex"])
def test_a_run_without_a_level_is_left_at_the_models_default(
    monkeypatch: pytest.MonkeyPatch, module: Any
) -> None:
    # As `collect` and `truth` run.
    for args in _command_lines(monkeypatch, module, None):
        assert "--effort" not in args
        assert not any("model_reasoning_effort" in arg for arg in args)


def test_every_run_of_a_question_is_at_its_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {"records": []}

    async def logged_in() -> LoginStatus:
        return LoginStatus(Login.LOGGED_IN, "claude.ai")

    async def split(
        program: object,
        question: str,
        holdings: object = None,
        *,
        series: object = None,
        effort: object = None,
    ) -> SplitOutcome:
        seen["split"] = effort
        return SplitOutcome()

    async def answer(
        system_prompt: str,
        input_text: str,
        *,
        on_start: Any,
        effort: object = None,
        on_usage: object = None,
    ) -> AsyncIterator[str]:
        seen["answer"] = effort
        yield "ok"

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        seen["records"].append(kwargs)

    monkeypatch.setattr(claude_code, "login_status", logged_in)
    monkeypatch.setattr(claude_code, "stream_answer", answer)
    monkeypatch.setattr(service, "split_question", split)
    monkeypatch.setattr(service, "_record", record)

    async def run() -> None:
        async for _ in service.answer_stream("q", [SECTION], effort=Effort.LOW):
            pass

    asyncio.run(run())

    assert seen["split"] is Effort.LOW
    assert seen["answer"] is Effort.LOW
    [kept] = seen["records"]
    assert kept["effort"] is Effort.LOW
