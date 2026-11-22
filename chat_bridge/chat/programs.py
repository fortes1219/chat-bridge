"""What the two answering programs share: their names, their login states and their errors.

Each program is a module with the same two functions, `login_status()` and `stream_answer()`,
so the service picks one from a table and nothing else changes with the program.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


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


class AnsweringProgram(Protocol):
    """What the service needs from a program's module."""

    async def login_status(self) -> LoginStatus: ...

    def stream_answer(
        self,
        system_prompt: str,
        input_text: str,
        *,
        on_start: Callable[[list[str]], None],
    ) -> AsyncIterator[str]: ...
