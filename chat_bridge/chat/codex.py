"""Runs the user's own logged-in Codex as an answering model.

Codex has the same permissions as Claude Code: it reads what the service hands it and writes the
answer, and it may not run commands, read or write files, or go online on the user's machine.
Each answer is one new `codex exec` process:
- every tool that would run a command, touch a file or go online is switched off, it works in an
  empty folder made for the call, and a read-only sandbox keeps the one tool that cannot be
  switched off, the patch tool, from writing. `codex exec` never asks for approval, so the
  sandbox's refusals stand;
- the rules, the sources and the question come in on standard input, so the command line holds
  no text from the user or the documents. On Windows npm installs Codex behind a `.cmd`
  launcher, which would re-read a command line holding line breaks or angle brackets;
- the key variables are taken out of its environment, so it answers from the user's login;
- no session is kept, as with Claude Code.

Codex reports the agent's message only once it is complete, so the answer arrives whole.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from asyncio.subprocess import Process
from collections.abc import AsyncIterator, Callable, Sequence
from pathlib import Path
from typing import Any

from chat_bridge.chat.programs import (
    Effort,
    Login,
    LoginStatus,
    ProgramError,
    Usage,
    UsageCallback,
    end_process_tree,
    token_count,
)

# The tools Codex turns on by default that would run a command, touch a file or go online. With
# them off it still reads what it is given and writes an answer, in a given format when asked.
DISABLED_FEATURES = (
    "shell_tool",  # runs commands
    "unified_exec",  # runs commands in a terminal
    "view_image",  # reads image files from the machine
    "image_generation",  # reads image files and saves the result to a file
    "computer_use",  # controls the machine
    "browser_use",  # goes online through a browser
    "apps",  # tools from connected outside services
    "plugins",  # adds tools and servers of its own
)
# Options that come before `exec`. Web search goes online; the single quotes make the value a
# TOML string that a Windows launcher passes through unchanged.
DISABLED_ARGS = tuple(
    arg for feature in DISABLED_FEATURES for arg in ("--disable", feature)
)
GLOBAL_ARGS = (*DISABLED_ARGS, "-c", "web_search='disabled'")
# A search of the web keeps every other tool off and turns live web search on: `exec` has no
# `--search` option, so the setting does it ("live" for live retrieval, Codex's configuration
# reference).
WEB_GLOBAL_ARGS = (*DISABLED_ARGS, "-c", "web_search='live'")
# One JSON event per line. No session is kept; the user's own configuration file is left out,
# because the servers, hooks and notify program set there could run commands, while the login
# is still read; and the sandbox is read-only, so the patch tool cannot write.
EXEC_ARGS = (
    "exec",
    "--ephemeral",
    "--skip-git-repo-check",
    "--ignore-user-config",
    "--sandbox",
    "read-only",
    "--json",
)
# Read the prompt from standard input.
STDIN_PROMPT = "-"
# With one of these set, Codex would use a key or token instead of the user's login.
STRIPPED_ENV = ("CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_API_KEY")
# `codex login status` exits 0 when credentials are present. It exits 1 both when they are not,
# printing this line, and when the check itself failed, so only this line means not logged in.
LOGGED_IN_EXIT_CODE = 0
NOT_LOGGED_IN_LINE = "Not logged in"
# Reading the login calls no model; a status slower than this means Codex is stuck.
LOGIN_STATUS_TIMEOUT_SECONDS = 15
# The same limit as Claude Code's answers: long enough for a slow answer, short enough that a
# stuck run cannot hold the request forever.
ANSWER_TIMEOUT_SECONDS = 600
# On Windows the child gets no console window of its own, so no window opens while answering.
CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
# How much of Codex's error output an error message quotes.
ERROR_TAIL_CHARS = 300
# The longest event line read: the completed message holds the whole answer.
MAX_LINE_BYTES = 1024 * 1024
# Codex reports a dropped connection it is retrying as an error event that is not a failure.
RETRY_PREFIX = "Reconnecting"


class CodexError(ProgramError):
    """Codex could not be run, or it reported an error. The message says which."""


class CodexNotFoundError(CodexError):
    """No `codex` on PATH or in its installer's folder. Only this means not installed; a `codex`
    that was found but refused is a different state."""


def child_env() -> dict[str, str]:
    """This process's environment without the key variables."""
    return {
        name: value for name, value in os.environ.items() if name not in STRIPPED_ENV
    }


def install_dir() -> Path | None:
    """The folder Codex's own installer puts it in: `CODEX_INSTALL_DIR` when set, else
    `%LOCALAPPDATA%\\Programs\\OpenAI\\Codex\\bin` on Windows and `~/.local/bin` elsewhere
    (openai/codex `scripts/install/install.ps1`, `install.sh`). The installer adds it to the
    user's PATH, but a service started before the install keeps the PATH it started with."""
    chosen = os.environ.get("CODEX_INSTALL_DIR")
    if chosen:
        return Path(chosen)
    if sys.platform != "win32":
        return Path.home() / ".local" / "bin"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data) / "Programs" / "OpenAI" / "Codex" / "bin"


def find_executable() -> str:
    """The `codex` the user installed: on PATH first, then in its installer's folder.

    On Windows the search looks in the current folder first, so a program of the same name put
    in the folder the service runs from would be found before the user's own. Such a program
    is refused, never run.
    """
    folder = install_dir()
    found = shutil.which("codex") or (
        shutil.which("codex", path=str(folder)) if folder else None
    )
    if found is None:
        raise CodexNotFoundError("Codex is not installed")
    if Path(found).resolve().is_relative_to(Path.cwd().resolve()):
        raise CodexError(
            f"the codex found is in the folder the service runs from: {found}"
        )
    return found


def effort_args(effort: Effort | None) -> tuple[str, ...]:
    """The level a run is started at, as a configuration value in single quotes like the web
    search one; none leaves the model's own default."""
    return () if effort is None else ("-c", f"model_reasoning_effort='{effort.value}'")


def command_line(
    executable: str, folder: str, effort: Effort | None = None
) -> list[str]:
    """How Codex is started for one answer, working in `folder`."""
    return [
        executable,
        *GLOBAL_ARGS,
        *effort_args(effort),
        *EXEC_ARGS,
        "--cd",
        folder,
        STDIN_PROMPT,
    ]


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
    """End Codex and every process it started (programs.end_process_tree)."""
    problem = await end_process_tree(process)
    if problem is not None:
        raise CodexError(f"Codex {problem}")


async def login_status() -> LoginStatus:
    """The local login as an answer sees it. Never raises."""
    try:
        executable = find_executable()
    except CodexNotFoundError as error:
        return LoginStatus(Login.NOT_INSTALLED, str(error))
    except CodexError as error:
        return LoginStatus(Login.UNKNOWN, str(error))
    try:
        process = await _start([executable, "login", "status"], with_input=False)
    except OSError as error:
        return LoginStatus(Login.UNKNOWN, f"Codex could not be started: {error}")
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), LOGIN_STATUS_TIMEOUT_SECONDS
        )
    except TimeoutError:
        detail = "`codex login status` did not reply in time"
        try:
            await _stop(process)
        except CodexError as error:
            detail = f"{detail}, and {error}"
        return LoginStatus(Login.UNKNOWN, detail)
    return login_from_exit(
        process.returncode, (stdout + stderr).decode(errors="replace")
    )


def login_from_exit(exit_code: int | None, output: str) -> LoginStatus:
    """Read `codex login status`: logged in only on exit 0, not logged in only when it says so."""
    lines = output.strip().splitlines()
    # Kept for errors and logs only; the first line names how Codex is signed in.
    detail = lines[0] if lines else f"exit code {exit_code}"
    if exit_code == LOGGED_IN_EXIT_CODE:
        return LoginStatus(Login.LOGGED_IN, detail)
    if detail == NOT_LOGGED_IN_LINE:
        return LoginStatus(Login.NOT_LOGGED_IN, detail)
    return LoginStatus(Login.UNKNOWN, detail)


def read_events(lines: list[bytes]) -> tuple[str | None, list[str]]:
    """The agent's last completed message, and the errors Codex reported, from its JSON events."""
    message: str | None = None
    errors: list[str] = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue  # Not an event; the exit code and the message decide success.
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                message = text if isinstance(text, str) else message
        elif kind == "error":
            text = str(event.get("message", ""))
            if not text.startswith(RETRY_PREFIX):
                errors.append(text)
        elif kind == "turn.failed":
            failure: Any = event.get("error")
            errors.append(
                str(failure.get("message"))
                if isinstance(failure, dict)
                else str(failure)
            )
    return message, errors


def usage_of(lines: list[bytes]) -> Usage | None:
    """The run's tokens from its last `turn.completed` event; None when there is none or a count is
    not a whole number.

    Codex's input count already holds what was read from and written to the cache, and its output
    count the reasoning (Codex's `TokenUsage`, filled from the API's counts), so nothing is added.
    """
    usage: Usage | None = None
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") != "turn.completed":
            continue
        counts = event.get("usage")
        if not isinstance(counts, dict):
            return None
        inputs, cached, outputs = (
            token_count(counts.get(name))
            for name in ("input_tokens", "cached_input_tokens", "output_tokens")
        )
        if inputs is None or cached is None or outputs is None:
            return None
        usage = Usage(inputs, cached, outputs)
    return usage


def _failure(
    message: str | None, errors: list[str], exit_code: int | None, stderr: str
) -> str | None:
    """Why the run failed, or None when it succeeded. Each rule can fail a run on its own."""
    tail = stderr.strip()[-ERROR_TAIL_CHARS:]
    if errors:
        return f"Codex reported an error: {errors[-1][:ERROR_TAIL_CHARS]}"
    if exit_code != 0:
        return f"Codex exited with code {exit_code}: {tail}"
    if not message:
        return f"Codex ended without an answer: {tail}"
    return None


def shaped_command_line(
    executable: str,
    folder: str,
    schema_file: str,
    global_args: Sequence[str] = GLOBAL_ARGS,
    effort: Effort | None = None,
) -> list[str]:
    """How Codex is started for a reply in the shape the schema file gives, working in `folder`."""
    return [
        executable,
        *global_args,
        *effort_args(effort),
        *EXEC_ARGS,
        "--output-schema",
        schema_file,
        "--cd",
        folder,
        STDIN_PROMPT,
    ]


async def reply_in_shape(
    system_prompt: str,
    input_text: str,
    schema: dict[str, Any],
    *,
    on_start: Callable[[list[str]], None],
    effort: Effort | None = None,
    on_usage: UsageCallback | None = None,
) -> dict[str, Any]:
    """Run Codex once, with no tools, for a reply in the given JSON shape, and return it.
    Raises CodexError when the run fails or its final message is not a JSON object."""
    return await _reply_in_shape(
        system_prompt, input_text, schema, GLOBAL_ARGS, on_start, effort, on_usage
    )


async def web_reply_in_shape(
    system_prompt: str,
    input_text: str,
    schema: dict[str, Any],
    sites: Sequence[str],
    *,
    on_start: Callable[[list[str]], None],
) -> dict[str, Any]:
    """Run Codex once, with live web search, for a reply in the given JSON shape. Codex's web
    search has no setting for sites, so `sites` limits nothing here; the caller checks what
    comes back. Raises CodexError as `reply_in_shape` does."""
    return await _reply_in_shape(
        system_prompt, input_text, schema, WEB_GLOBAL_ARGS, on_start
    )


async def _reply_in_shape(
    system_prompt: str,
    input_text: str,
    schema: dict[str, Any],
    global_args: Sequence[str],
    on_start: Callable[[list[str]], None],
    effort: Effort | None = None,
    on_usage: UsageCallback | None = None,
) -> dict[str, Any]:
    """The schema goes in a file of its own folder, so the working folder stays empty and the
    command line holds only the file's path."""
    with (
        tempfile.TemporaryDirectory(prefix="chat-bridge-codex-") as folder,
        tempfile.TemporaryDirectory(prefix="chat-bridge-schema-") as schema_folder,
    ):
        schema_file = Path(schema_folder) / "schema.json"
        schema_file.write_text(json.dumps(schema), encoding="utf-8")
        args = shaped_command_line(
            find_executable(), folder, str(schema_file), global_args, effort
        )
        on_start(args)
        process = await _start(args, with_input=True)
        try:
            message = await _read_answer(
                process, f"{system_prompt}\n\n{input_text}", on_usage
            )
        finally:
            await _stop(process)
    return shaped_reply(message)


def shaped_reply(message: str) -> dict[str, Any]:
    """The final message as the JSON object `--output-schema` asked for."""
    try:
        reply = json.loads(message)
    except ValueError:
        raise CodexError("Codex's reply is not JSON") from None
    if not isinstance(reply, dict):
        raise CodexError("Codex's reply is not a JSON object")
    return reply


async def stream_answer(
    system_prompt: str,
    input_text: str,
    *,
    on_start: Callable[[list[str]], None],
    effort: Effort | None = None,
    on_usage: UsageCallback | None = None,
) -> AsyncIterator[str]:
    """Yield the answer once Codex has written it.

    `on_start` gets the command line just before the process starts, so the caller can keep it
    as evidence of how the model ran. Raises CodexError when Codex fails or runs past the time
    limit.
    """
    with tempfile.TemporaryDirectory(prefix="chat-bridge-codex-") as folder:
        args = command_line(find_executable(), folder, effort)
        on_start(args)
        process = await _start(args, with_input=True)
        try:
            answer = await _read_answer(
                process, f"{system_prompt}\n\n{input_text}", on_usage
            )
        finally:
            await _stop(process)
    yield answer


async def _read_answer(
    process: Process, input_text: str, on_usage: UsageCallback | None = None
) -> str:
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise CodexError("Codex started without its pipes")
    try:
        process.stdin.write(input_text.encode("utf-8"))
        await process.stdin.drain()
        process.stdin.close()
    except (BrokenPipeError, ConnectionResetError):
        pass  # The child ended early; its output and exit code below say why.
    try:
        stdout, stderr = await asyncio.wait_for(
            asyncio.gather(_read_lines(process.stdout), process.stderr.read()),
            ANSWER_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise CodexError(
            f"Codex did not finish within {ANSWER_TIMEOUT_SECONDS} seconds"
        ) from None
    exit_code = await process.wait()
    message, errors = read_events(stdout)
    # A run that failed may still have used tokens; its last event says how many.
    usage = usage_of(stdout)
    if on_usage is not None and usage is not None:
        on_usage(usage)
    failure = _failure(
        message, errors, exit_code, stderr.decode("utf-8", errors="replace")
    )
    if failure or message is None:
        raise CodexError(failure or "Codex ended without an answer")
    return message


async def _read_lines(stream: asyncio.StreamReader) -> list[bytes]:
    lines: list[bytes] = []
    while line := await stream.readline():
        lines.append(line)
    return lines
