"""How Claude Code is started and judged, without starting it."""

import asyncio
import json
import shutil
import sys
from pathlib import Path

import psutil
import pytest

from chat_bridge.chat import claude_code
from chat_bridge.chat.claude_code import Login, LoginStatus
from chat_bridge.chat.service import NO_LOGIN_MESSAGES, NoLoginError
from tests.chat.conftest import StartLauncher


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


# --- The split run ---------------------------------------------------------------------------

SPLIT_QUESTION = "<question>\n台積電與 0050 的變化？\n</question>\n"


class _FinishedProcess:
    """Stands in for a `claude -p --output-format json` run that printed `output` and ended."""

    def __init__(self, output: bytes, exit_code: int = 0) -> None:
        self.output = output
        self.returncode = exit_code
        self.input: bytes | None = None

    async def communicate(self, data: bytes) -> tuple[bytes, bytes]:
        self.input = data
        return self.output, b""


def test_the_split_asks_for_its_shape_with_tools_off_and_the_question_on_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: dict[str, object] = {}
    result = {
        "type": "result",
        "is_error": False,
        "structured_output": {"parts": ["台積電"]},
    }

    async def fake_start(args: list[str], *, with_input: bool) -> object:
        started["args"] = args
        started["process"] = _FinishedProcess(json.dumps(result).encode())
        return started["process"]

    monkeypatch.setattr(claude_code, "find_executable", lambda: "claude")
    monkeypatch.setattr(claude_code, "_start", fake_start)
    told: list[str] = []
    schema = {"type": "object", "properties": {"parts": {"type": "array"}}}

    reply = asyncio.run(
        claude_code.reply_in_shape(
            "rules", SPLIT_QUESTION, schema, on_start=told.extend
        )
    )

    assert reply == {"parts": ["台積電"]}
    args = started["args"]
    assert isinstance(args, list)
    assert told == args
    assert args[args.index("--json-schema") + 1] == json.dumps(
        schema, separators=(",", ":")
    )
    assert args[args.index("--output-format") + 1] == "json"
    assert args[args.index("--tools") + 1] == ""
    assert "--restricted" in args and "--strict-mcp-config" in args
    assert "台積電" not in " ".join(args)
    process = started["process"]
    assert isinstance(process, _FinishedProcess)
    assert process.input == SPLIT_QUESTION.encode()


@pytest.mark.parametrize(
    ("output", "exit_code", "reason"),
    [
        (b"not json", 0, "ended without a result"),
        (
            json.dumps({"type": "result", "is_error": True, "result": "x"}).encode(),
            0,
            "reported an error",
        ),
        (
            json.dumps({"type": "result", "is_error": False, "result": "x"}).encode(),
            0,
            "asked-for shape",
        ),
        (
            json.dumps({"type": "result", "structured_output": ["a"]}).encode(),
            0,
            "asked-for shape",
        ),
        (
            json.dumps({"type": "result", "structured_output": {"parts": []}}).encode(),
            1,
            "exited with code 1",
        ),
    ],
)
def test_a_split_run_without_a_reply_in_its_shape_fails(
    output: bytes, exit_code: int, reason: str
) -> None:
    with pytest.raises(claude_code.ClaudeCodeError, match=reason):
        claude_code.shaped_reply(output, exit_code, "")


ECHO_FIRST_ARGUMENT = (
    "import sys\nsys.stdout.buffer.write(sys.argv[1].encode('utf-8'))\n"
)


def _arrives_unchanged(args: list[str]) -> str:
    async def run() -> str:
        process = await claude_code._start(args, with_input=False)
        output, _ = await process.communicate()
        return output.decode("utf-8")

    return asyncio.run(run())


def test_the_schema_reaches_an_executable_unchanged(tmp_path: Path) -> None:
    from chat_bridge.chat.split import SPLIT_SCHEMA

    script = tmp_path / "echo.py"
    script.write_text(ECHO_FIRST_ARGUMENT, encoding="utf-8")
    schema = json.dumps(SPLIT_SCHEMA, separators=(",", ":"))

    assert _arrives_unchanged([sys.executable, "-I", str(script), schema]) == schema


@pytest.mark.skipif(
    sys.platform != "win32", reason="a .cmd launcher exists only on Windows"
)
def test_the_schema_reaches_a_cmd_launcher_unchanged(tmp_path: Path) -> None:
    from chat_bridge.chat.split import SPLIT_SCHEMA

    # An npm install of Claude Code is a .cmd launcher, which cmd.exe reads before node does.
    script = tmp_path / "echo.py"
    script.write_text(ECHO_FIRST_ARGUMENT, encoding="utf-8")
    launcher = tmp_path / "claude.cmd"
    launcher.write_text(f'@"{sys.executable}" -I "{script}" %*\r\n', encoding="utf-8")
    schema = json.dumps(SPLIT_SCHEMA, separators=(",", ":"))

    assert _arrives_unchanged([str(launcher), schema]) == schema


@pytest.mark.skipif(
    sys.platform != "win32", reason="a .cmd launcher exists only on Windows"
)
def test_a_stop_ends_claude_code_and_everything_it_started(
    start_launcher: StartLauncher,
) -> None:
    # Ending only the launcher left Claude Code writing the answer after the person stopped it,
    # and holding the output pipes.
    async def run() -> list[psutil.Process]:
        process, below = await start_launcher(claude_code._start)
        await claude_code._stop(process)
        return below

    below = asyncio.run(run())

    assert not [child for child in below if child.is_running()]
