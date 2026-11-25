"""The path a shell word names, following the variables and the cd earlier in the same command."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from utils.places import TEMP_DIR

DRIVE_PATH = re.compile(r"^/([a-zA-Z])(/|$)")
# $NAME, ${NAME}, $env:NAME and %NAME% are read from variables set earlier in the same command,
# then from the environment, which the hook process inherits from the session.
VARIABLE = re.compile(r"\$\{(\w+)\}|\$env:(\w+)|\$(\w+)|%(\w+)%", re.IGNORECASE)
ASSIGNMENT = re.compile(r"^\$?(\w+)=(.*)$", re.DOTALL)
# Git Bash on Windows: "$(cygpath -w <path>)" names the same path in Windows form.
CYGPATH = re.compile(r"^\$\(cygpath\s+-[wmu]\s+(\S+)\)$")
DECLARING_WORDS = {"export", "local", "declare", "readonly"}
UNRESOLVED_MARKS = ("$", "%", "*", "`", "?")


@dataclass
class ShellState:
    """What the shell knows at a point in the command: the working directory and the variables set."""

    base: Path | None  # None after a cd this guard could not follow
    variables: dict[str, str]


def take_assignments(words: list[str], state: ShellState) -> list[str]:
    """Records NAME=value (and PowerShell's $name = value) and returns the words after them."""
    if len(words) == 3 and words[0].startswith("$") and words[1] == "=":
        state.variables[words[0][1:].lower()] = expand(words[2], state)
        return []
    if len(words) > 3 and words[0].startswith("$") and words[1] == "=":
        return words[
            2:
        ]  # $name = <command>: the command is checked, the value is not known
    index = 1 if words and words[0] in DECLARING_WORDS else 0
    while index < len(words):
        match = ASSIGNMENT.match(words[index])
        if match is None:
            break
        state.variables[match.group(1).lower()] = expand(match.group(2), state)
        index += 1
    return words[index:]


def expand(text: str, state: ShellState) -> str:
    def value(match: re.Match[str]) -> str:
        name = next(group for group in match.groups() if group)
        known = state.variables.get(name.lower()) or os.environ.get(name)
        if known is None and name.upper() == "HOME":
            known = str(Path.home())
        return known if known is not None else match.group(0)

    return VARIABLE.sub(value, text)


def shell_path(word: str, state: ShellState) -> Path | None:
    """The absolute path a shell word names, or None when its folder depends on something unknown.

    When only the file name is unknown (`sfb_$id.html`), the folder decides.
    """
    folder, separator, name = normalized(word, state).rpartition("/")
    if any(mark in folder for mark in UNRESOLVED_MARKS):
        return None
    if any(mark in name for mark in UNRESOLVED_MARKS):
        name = "unresolved-name"
    return absolute(f"{folder}{separator}{name}", state)


def known_folder(word: str, state: ShellState) -> Path | None:
    """The deepest folder of a shell word that does not depend on something unknown, as
    `<scratch>` for `$S/$run/out.txt` when only S is known; None when even that is unknown."""
    text = normalized(word, state)
    unknown = min(
        (text.index(mark) for mark in UNRESOLVED_MARKS if mark in text),
        default=len(text),
    )
    folder = text[:unknown].rpartition("/")[0]
    return absolute(folder, state) if folder else None


def normalized(word: str, state: ShellState) -> str:
    """The word with its variables, cygpath, ~, /tmp and /c/ drive prefix turned into a path."""
    converted = CYGPATH.match(word.strip())
    text = expand(converted.group(1) if converted else word, state).replace("\\", "/")
    if text.startswith("~"):
        text = Path.home().as_posix() + text[1:]
    if text == "/tmp" or text.startswith("/tmp/"):
        text = TEMP_DIR.as_posix() + text[4:]
    drive = DRIVE_PATH.match(text)
    if drive:
        text = f"{drive.group(1)}:/{text[drive.end() :]}"
    return text


def absolute(text: str, state: ShellState) -> Path | None:
    path = Path(text)
    if not path.is_absolute():
        if state.base is None:
            return None
        path = state.base / path
    try:
        return path.resolve()
    except OSError:
        return None
