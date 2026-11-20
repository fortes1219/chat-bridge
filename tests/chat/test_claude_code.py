"""How Claude Code is started and judged, without starting it."""

import asyncio
import json
import shutil
from pathlib import Path

import pytest

from chat_bridge.chat import claude_code
from chat_bridge.chat.claude_code import Login, LoginStatus
from chat_bridge.chat.service import NO_LOGIN_MESSAGES, NoLoginError


def test_the_key_variables_are_removed_from_the_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in claude_code.STRIPPED_ENV:
        monkeypatch.setenv(name, "sk-test")
    monkeypatch.setenv("CHAT_BRIDGE_TEST_KEEP", "kept")

    env = claude_code.child_env()

    assert not set(claude_code.STRIPPED_ENV) & set(env)
    assert env["CHAT_BRIDGE_TEST_KEEP"] == "kept"


@pytest.mark.parametrize(
    ("output", "state", "detail"),
    [
        pytest.param(
            {"loggedIn": True, "authMethod": "claude.ai"},
            Login.LOGGED_IN,
            "claude.ai",
            id="logged in",
        ),
        pytest.param(
            {"loggedIn": False, "authMethod": "none"},
            Login.NOT_LOGGED_IN,
            "none",
            id="logged out",
        ),
        pytest.param(
            {"loggedIn": "true"}, Login.NOT_LOGGED_IN, "none", id="not a JSON true"
        ),
        pytest.param({}, Login.NOT_LOGGED_IN, "none", id="no field"),
    ],
)
def test_only_a_json_true_counts_as_logged_in(
    output: dict[str, object], state: Login, detail: str
) -> None:
    status = claude_code.login_from_status(json.dumps(output).encode())

    assert status.state is state
    assert status.detail == detail


@pytest.mark.parametrize(
    "output", [b"", b"Logged in as someone", b"[true]"], ids=["empty", "text", "a list"]
)
def test_a_status_that_cannot_be_read_is_unknown_and_not_a_login(
    output: bytes,
) -> None:
    status = claude_code.login_from_status(output)

    assert status.state is Login.UNKNOWN


def test_a_missing_executable_is_reported_as_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(claude_code, "FALLBACK_EXECUTABLE", Path("no-such-claude"))

    status = asyncio.run(claude_code.login_status())

    assert status.state is Login.NOT_INSTALLED


@pytest.mark.parametrize(
    "state", [Login.NOT_INSTALLED, Login.NOT_LOGGED_IN, Login.UNKNOWN]
)
def test_each_state_without_a_login_has_its_own_message(state: Login) -> None:
    message = str(NoLoginError(LoginStatus(state, "why")))

    assert message == NO_LOGIN_MESSAGES[state].format(detail="why")
    assert len({*NO_LOGIN_MESSAGES.values()}) == len(NO_LOGIN_MESSAGES)


SUCCESS = {"type": "result", "is_error": False, "result": "ok"}


def test_a_run_with_a_result_and_exit_code_0_succeeded() -> None:
    assert claude_code._failure(SUCCESS, 0, "") is None


@pytest.mark.parametrize(
    ("result", "exit_code", "reason"),
    [
        pytest.param(None, 0, "ended without a result", id="no result"),
        pytest.param(
            {"type": "result", "is_error": True, "result": "overloaded"},
            0,
            "reported an error",
            id="an error result",
        ),
        pytest.param(SUCCESS, 1, "exited with code 1", id="exit code 1"),
    ],
)
def test_each_failure_rule_fails_the_run_on_its_own(
    result: dict[str, object] | None, exit_code: int, reason: str
) -> None:
    failure = claude_code._failure(result, exit_code, "")

    assert failure is not None
    assert reason in failure
