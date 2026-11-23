"""Which program answers, and what the login states show, without starting either program."""

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import date
from typing import Any

import pytest

from chat_bridge.chat import claude_code, codex, service
from chat_bridge.chat.programs import Login, LoginStatus, Program
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
ACCOUNT = "someone@example.com"
# Each fake program answers with its own name.
NAMED = {"claude": Program.CLAUDE_CODE, "codex": Program.CODEX}


def _logins(
    monkeypatch: pytest.MonkeyPatch, claude: Login, codex_state: Login
) -> list[dict[str, Any]]:
    """Set each program's login, make each answer with its own name, and keep what is recorded."""
    written: list[dict[str, Any]] = []

    async def record(question: str, answer: str, sections: Any, **kwargs: Any) -> None:
        written.append({"answer": answer, **kwargs})

    def login(state: Login) -> Callable[[], Any]:
        async def status() -> LoginStatus:
            return LoginStatus(state, ACCOUNT)

        return status

    def answer(name: str) -> Callable[..., AsyncIterator[str]]:
        async def pieces(
            system_prompt: str,
            input_text: str,
            *,
            on_start: Callable[[list[str]], None],
        ) -> AsyncIterator[str]:
            on_start([name])
            yield name

        return pieces

    monkeypatch.setattr(service, "_record", record)
    monkeypatch.setattr(claude_code, "login_status", login(claude))
    monkeypatch.setattr(codex, "login_status", login(codex_state))
    monkeypatch.setattr(claude_code, "stream_answer", answer("claude"))
    monkeypatch.setattr(codex, "stream_answer", answer("codex"))
    return written


def _ask(requested: Program | None) -> tuple[list[ChatDelta], Exception | None]:
    async def run() -> tuple[list[ChatDelta], Exception | None]:
        deltas: list[ChatDelta] = []
        try:
            async for delta in service.answer_stream("q", [SECTION], requested):
                deltas.append(delta)
        except Exception as error:
            return deltas, error
        return deltas, None

    return asyncio.run(run())


@pytest.mark.parametrize(
    ("claude", "codex_state", "requested", "answered"),
    [
        pytest.param(
            Login.LOGGED_IN, Login.LOGGED_IN, None, "claude", id="both, none named"
        ),
        pytest.param(
            Login.LOGGED_IN,
            Login.LOGGED_IN,
            Program.CODEX,
            "codex",
            id="both, Codex named",
        ),
        pytest.param(
            Login.LOGGED_IN,
            Login.LOGGED_IN,
            Program.CLAUDE_CODE,
            "claude",
            id="both, Claude Code named",
        ),
        pytest.param(
            Login.NOT_LOGGED_IN, Login.LOGGED_IN, None, "codex", id="only Codex"
        ),
        pytest.param(
            Login.LOGGED_IN, Login.NOT_INSTALLED, None, "claude", id="only Claude Code"
        ),
    ],
)
def test_the_chosen_program_answers_and_is_named(
    monkeypatch: pytest.MonkeyPatch,
    claude: Login,
    codex_state: Login,
    requested: Program | None,
    answered: str,
) -> None:
    written = _logins(monkeypatch, claude, codex_state)

    deltas, error = _ask(requested)

    assert error is None
    assert deltas[0].context is not None
    assert deltas[0].context.program == NAMED[answered]
    assert deltas[1].delta == answered
    [record] = written
    assert record["program"] == deltas[0].context.program
    assert record["command_line"] == [answered]


@pytest.mark.parametrize(
    ("requested", "message"),
    [
        pytest.param(
            Program.CODEX,
            service.CODEX_NO_LOGIN_MESSAGES[Login.NOT_LOGGED_IN],
            id="Codex named",
        ),
        pytest.param(
            Program.CLAUDE_CODE,
            service.NO_LOGIN_MESSAGES[Login.NOT_LOGGED_IN],
            id="Claude Code named",
        ),
    ],
)
def test_a_named_program_that_is_not_logged_in_is_refused_not_swapped(
    monkeypatch: pytest.MonkeyPatch, requested: Program, message: str
) -> None:
    other_logged_in = (
        (Login.LOGGED_IN, Login.NOT_LOGGED_IN)
        if requested is Program.CODEX
        else (Login.NOT_LOGGED_IN, Login.LOGGED_IN)
    )
    written = _logins(monkeypatch, *other_logged_in)

    deltas, error = _ask(requested)

    assert isinstance(error, service.NoLoginError)
    assert str(error) == message
    assert [delta.type for delta in deltas] == ["response.context"]
    [record] = written
    assert record["error"] == message
    assert record["command_line"] is None


def test_with_neither_logged_in_the_refusal_says_how_to_log_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _logins(monkeypatch, Login.NOT_INSTALLED, Login.NOT_INSTALLED)

    _, error = _ask(None)

    assert isinstance(error, service.NoLoginError)
    assert "claude auth login" in str(error)
    assert "codex login" in str(error)


def test_the_login_states_show_each_program_and_never_its_own_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _logins(monkeypatch, Login.LOGGED_IN, Login.UNKNOWN)

    states = asyncio.run(service.program_states())

    assert [(s.program, s.state) for s in states] == [
        (Program.CLAUDE_CODE, Login.LOGGED_IN),
        (Program.CODEX, Login.UNKNOWN),
    ]
    assert all(ACCOUNT not in state.model_dump_json() for state in states)


@pytest.mark.parametrize(
    "state", [Login.NOT_INSTALLED, Login.NOT_LOGGED_IN, Login.UNKNOWN]
)
def test_each_codex_state_without_a_login_has_its_own_message(state: Login) -> None:
    message = str(service.NoLoginError(LoginStatus(state, "why"), Program.CODEX))

    assert message == service.CODEX_NO_LOGIN_MESSAGES[state].format(detail="why")
    assert len({*service.CODEX_NO_LOGIN_MESSAGES.values()}) == len(
        service.CODEX_NO_LOGIN_MESSAGES
    )


def test_an_unexpected_error_still_leaves_the_question_on_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    written = _logins(monkeypatch, Login.LOGGED_IN, Login.LOGGED_IN)

    async def cannot_start(
        system_prompt: str, input_text: str, *, on_start: Callable[[list[str]], None]
    ) -> AsyncIterator[str]:
        raise OSError("the program was moved")
        yield ""  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(codex, "stream_answer", cannot_start)

    _, error = _ask(Program.CODEX)

    assert isinstance(error, OSError)
    [record] = written
    assert record["error"] == "OSError: the program was moved"
    assert record["program"] == Program.CODEX
