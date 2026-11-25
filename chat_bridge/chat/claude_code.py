"""Runs the user's own logged-in Claude Code as an answering model that can only write text.

Each answer is one new `claude -p` process:
- every built-in tool and MCP server is off, and no session is saved, so whatever a question or
  a document talks the model into, it can only write text;
- the system prompt comes from a file, and the sources and the question come in on standard
  input, so the command line holds no text from the user or the documents;
- the child signs in with the local Claude Code login only: the key variables are taken out of
  its environment, so a key in the user's shell is never billed.

The answer streams: Claude Code writes one JSON message per line, partial messages included,
and each text piece is passed on as it arrives, so the user reads the answer while it is written.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from asyncio.subprocess import Process
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

from chat_bridge.chat.programs import (
    Login,
    LoginStatus,
    ProgramError,
    end_process_tree,
)

# Nothing from the user's own Claude Code setup (settings, hooks, MCP servers), no built-in
# tools, and no session saved to disk. With no tools the model can only write text, and the
# user's setup cannot give it any.
ISOLATION_ARGS = (
    "--restricted",
    "--strict-mcp-config",
    "--tools",
    "",
    "--no-session-persistence",
)
# One JSON message per line, partial messages included, so pieces of the answer can be passed
# on before the answer ends.
STREAM_ARGS = (
    "--output-format",
    "stream-json",
    "--verbose",
    "--include-partial-messages",
)
# One JSON result at the end, holding a reply in the shape the schema after these gives.
SHAPED_ARGS = ("--output-format", "json", "--json-schema")
# With one of these set, `claude -p` would use a key instead of the user's login, and bill an
# account the user may not know is set.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")
# The native installer puts the executable here, and it is not always on PATH yet.
FALLBACK_EXECUTABLE = Path.home() / ".local" / "bin" / "claude"
# Reading the login calls no model. A status that takes longer than this means Claude Code is
# stuck, and the question is better refused than left waiting.
LOGIN_STATUS_TIMEOUT_SECONDS = 15
# One answer reads eight whole sections and may write at length. A shorter limit would cut off
# answers that are slow but working; past this, a stuck run is stopped so it cannot hold the
# request forever.
ANSWER_TIMEOUT_SECONDS = 600
# On Windows the child gets no console window of its own, so no window opens while answering.
CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
# How much of Claude Code's error output an error message quotes.
ERROR_TAIL_CHARS = 300
# The longest output line read. A line holds one message, and the final result holds the whole
# answer; asyncio's default of 64 KB could cut a long answer, so lines up to 1 MB are read.
MAX_LINE_BYTES = 1024 * 1024


__all__ = [
    "ClaudeCodeError",
    "Login",
    "LoginStatus",
    "login_status",
    "reply_in_shape",
    "stream_answer",
]


class ClaudeCodeError(ProgramError):
    """Claude Code could not be run, or it reported an error. The message says which."""


def child_env() -> dict[str, str]:
    """This process's environment without the key variables."""
    return {
        name: value for name, value in os.environ.items() if name not in STRIPPED_ENV
    }


def find_executable() -> str:
    """The `claude` executable: on PATH first, then where the native installer puts it."""
    found = shutil.which("claude")
    if found:
        return found
    if FALLBACK_EXECUTABLE.is_file():
        return str(FALLBACK_EXECUTABLE)
    raise ClaudeCodeError("Claude Code is not installed")


async def _start(args: list[str], *, with_input: bool) -> Process:
    return await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE if with_input else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=child_env(),
        creationflags=CREATION_FLAGS,
        limit=MAX_LINE_BYTES,
    )


async def _stop(process: Process) -> None:
    """End Claude Code and every process it started (programs.end_process_tree).

    An npm install is a `.cmd` launcher in front of node; ending only the launcher left Claude
    Code writing the answer after the person stopped it.
    """
    problem = await end_process_tree(process)
    if problem is not None:
        raise ClaudeCodeError(f"Claude Code {problem}")


async def login_status() -> LoginStatus:
    """The local login as an answer sees it. Never raises.

    It runs with the same environment as an answer, so a key that an answer would not use
    does not count as a login.
    """
    try:
        executable = find_executable()
    except ClaudeCodeError as error:
        return LoginStatus(Login.NOT_INSTALLED, str(error))
    try:
        process = await _start([executable, "auth", "status"], with_input=False)
    except OSError as error:
        return LoginStatus(Login.UNKNOWN, f"Claude Code could not be started: {error}")
    try:
        output, _ = await asyncio.wait_for(
            process.communicate(), LOGIN_STATUS_TIMEOUT_SECONDS
        )
    except TimeoutError:
        detail = "`claude auth status` did not reply in time"
        try:
            await _stop(process)
        except ClaudeCodeError as error:
            detail = f"{detail}, and {error}"
        return LoginStatus(Login.UNKNOWN, detail)
    return login_from_status(output)


def login_from_status(output: bytes) -> LoginStatus:
    """Read the JSON `claude auth status` prints. Only `"loggedIn": true` counts as logged in."""
    try:
        payload = json.loads(output)
    except ValueError:
        return LoginStatus(Login.UNKNOWN, "the login status is not JSON")
    if not isinstance(payload, dict):
        return LoginStatus(Login.UNKNOWN, "the login status is not a JSON object")
    state = Login.LOGGED_IN if payload.get("loggedIn") is True else Login.NOT_LOGGED_IN
    return LoginStatus(state, str(payload.get("authMethod") or "none"))


def _text_piece(message: dict[str, Any]) -> str | None:
    """The text a partial message adds, if any. It holds one raw API stream event."""
    if message.get("type") != "stream_event":
        return None
    event = message.get("event")
    if not isinstance(event, dict) or event.get("type") != "content_block_delta":
        return None
    delta = event.get("delta")
    if not isinstance(delta, dict) or delta.get("type") != "text_delta":
        return None
    text = delta.get("text")
    return text if isinstance(text, str) else None


def _failure(
    result: dict[str, Any] | None, exit_code: int | None, stderr: str
) -> str | None:
    """Why the run failed, or None when it succeeded.

    Each of the three can happen without the others: Claude Code can exit 0 and still report an
    error in its result, or stop before it writes a result at all.
    """
    tail = stderr.strip()[-ERROR_TAIL_CHARS:]
    if result is None:
        return f"Claude Code ended without a result (exit code {exit_code}): {tail}"
    if result.get("is_error") is True:
        return f"Claude Code reported an error: {str(result.get('result'))[:ERROR_TAIL_CHARS]}"
    if exit_code != 0:
        return f"Claude Code exited with code {exit_code}: {tail}"
    return None


async def reply_in_shape(
    system_prompt: str,
    input_text: str,
    schema: dict[str, Any],
    *,
    on_start: Callable[[list[str]], None],
) -> dict[str, Any]:
    """Run Claude Code once for a reply in the given JSON shape, and return it.

    The schema is fixed text, so it may be on the command line; the input goes on standard
    input. Raises ClaudeCodeError when the run fails or ends without a reply in that shape.
    """
    with tempfile.TemporaryDirectory(prefix="chat-bridge-") as folder:
        prompt_file = Path(folder) / "system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        args = [
            find_executable(),
            "-p",
            *ISOLATION_ARGS,
            *SHAPED_ARGS,
            json.dumps(schema, separators=(",", ":")),
            "--system-prompt-file",
            str(prompt_file),
        ]
        on_start(args)
        process = await _start(args, with_input=True)
        try:
            output, stderr = await process.communicate(input_text.encode("utf-8"))
        finally:
            await _stop(process)
    return shaped_reply(
        output, process.returncode, stderr.decode("utf-8", errors="replace")
    )


def shaped_reply(output: bytes, exit_code: int | None, stderr: str) -> dict[str, Any]:
    """The reply in the asked-for shape from the JSON result `--output-format json` prints."""
    try:
        result = json.loads(output)
    except ValueError:
        result = None
    if not isinstance(result, dict):
        result = None
    failure = _failure(result, exit_code, stderr)
    if failure:
        raise ClaudeCodeError(failure)
    # A run that ends without valid structured output, for example because the model declined,
    # has no such field (headless.md, "Get structured output").
    reply = result.get("structured_output") if result else None
    if not isinstance(reply, dict):
        raise ClaudeCodeError(
            "Claude Code ended without a reply in the asked-for shape"
        )
    return reply


async def stream_answer(
    system_prompt: str,
    input_text: str,
    *,
    on_start: Callable[[list[str]], None],
) -> AsyncIterator[str]:
    """Yield the answer's text pieces as Claude Code writes them.

    `on_start` gets the command line just before the process starts, so the caller can keep it
    as evidence of how the model ran. When no partial message comes through, the whole answer
    from the final result is yielded once instead. Raises ClaudeCodeError when Claude Code
    fails or runs past the time limit.
    """
    with tempfile.TemporaryDirectory(prefix="chat-bridge-") as folder:
        prompt_file = Path(folder) / "system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        args = [
            find_executable(),
            "-p",
            *ISOLATION_ARGS,
            *STREAM_ARGS,
            "--system-prompt-file",
            str(prompt_file),
        ]
        on_start(args)
        process = await _start(args, with_input=True)
        try:
            async for piece in _read_answer(process, input_text):
                yield piece
        finally:
            await _stop(process)


async def _read_answer(process: Process, input_text: str) -> AsyncIterator[str]:
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise ClaudeCodeError("Claude Code started without its pipes")
    try:
        process.stdin.write(input_text.encode("utf-8"))
        await process.stdin.drain()
        process.stdin.close()
    except (BrokenPipeError, ConnectionResetError):
        pass  # The child ended early; its output and exit code below say why.
    # Read the error output alongside, so a full pipe cannot stall the child.
    stderr_task = asyncio.create_task(process.stderr.read())

    deadline = asyncio.get_running_loop().time() + ANSWER_TIMEOUT_SECONDS
    result: dict[str, Any] | None = None
    streamed = False
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        try:
            line = await asyncio.wait_for(process.stdout.readline(), max(remaining, 0))
        except TimeoutError:
            stderr_task.cancel()
            raise ClaudeCodeError(
                f"Claude Code did not finish within {ANSWER_TIMEOUT_SECONDS} seconds"
            ) from None
        if not line:
            break
        try:
            message = json.loads(line)
        except ValueError:
            continue  # Not a message; the result line decides success.
        if not isinstance(message, dict):
            continue
        piece = _text_piece(message)
        if piece:
            streamed = True
            yield piece
        if message.get("type") == "result":
            result = message

    exit_code = await process.wait()
    stderr = (await stderr_task).decode("utf-8", errors="replace")
    failure = _failure(result, exit_code, stderr)
    if failure:
        raise ClaudeCodeError(failure)
    final_text = result.get("result") if result else None
    if not streamed and isinstance(final_text, str):
        yield final_text
