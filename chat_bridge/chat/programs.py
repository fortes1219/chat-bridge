"""What the two answering programs share: their names, their login states, their errors, and how
they are stopped.

Each program is a module with the same four functions, `login_status()`, `reply_in_shape()`,
`web_reply_in_shape()` and `stream_answer()`, so the service picks one from a table and nothing
else changes with the program.
"""

import asyncio
from asyncio.subprocess import Process
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

import psutil

# How long a stopped program, and every process it started, may take to end.
STOP_TIMEOUT_SECONDS = 10


class Program(StrEnum):
    CLAUDE_CODE = "claude-code"
    CODEX = "codex"


class Login(StrEnum):
    LOGGED_IN = "logged in"
    NOT_LOGGED_IN = "not logged in"
    NOT_INSTALLED = "not installed"
    # The status could not be read. It is never taken for a login.
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LoginStatus:
    state: Login
    # How the program says it is signed in, or why the state is unknown. Kept for errors and
    # logs, never sent to the client: a program's own status text can name the account.
    detail: str


class ProgramError(Exception):
    """An answering program could not be run, or it reported an error. The message says which."""


async def end_process_tree(process: Process) -> str | None:
    """End a program and every process it started; why that failed, or None when all ended.

    On Windows npm installs Claude Code and Codex behind a `.cmd` launcher that starts node, which
    starts the program. Killing the launcher alone would leave the program answering, on the
    user's plan, and holding the output pipes: the pipes never reach their end, so they are left
    for the garbage collector, which after the service has ended prints "I/O operation on closed
    pipe". The processes below it are listed before the kill, because a killed parent no longer
    leads to them. Every kill is sent before the first wait, so a stop that a cancelled request
    interrupts has still ended them all.
    """
    if process.returncode is not None:
        return None
    try:
        below = psutil.Process(process.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        below = []
    process.kill()
    for child in below:
        # One that cannot be killed is left for the check below, which reports it.
        with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
            child.kill()
    _, alive = await asyncio.to_thread(
        psutil.wait_procs, below, timeout=STOP_TIMEOUT_SECONDS
    )
    if alive:
        pids = ", ".join(str(child.pid) for child in alive)
        return f"left processes running after the stop: {pids}"
    try:
        await asyncio.wait_for(process.wait(), STOP_TIMEOUT_SECONDS)
    except TimeoutError:
        return f"did not stop within {STOP_TIMEOUT_SECONDS} seconds"
    return None


class AnsweringProgram(Protocol):
    """What the service needs from a program's module."""

    async def login_status(self) -> LoginStatus: ...

    async def reply_in_shape(
        self,
        system_prompt: str,
        input_text: str,
        schema: dict[str, Any],
        *,
        on_start: Callable[[list[str]], None],
    ) -> dict[str, Any]: ...

    async def web_reply_in_shape(
        self,
        system_prompt: str,
        input_text: str,
        schema: dict[str, Any],
        sites: Sequence[str],
        *,
        on_start: Callable[[list[str]], None],
    ) -> dict[str, Any]: ...

    def stream_answer(
        self,
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
    ) -> AsyncIterator[str]: ...
