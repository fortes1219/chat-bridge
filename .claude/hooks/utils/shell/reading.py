"""One simple command as the shell runs it: its name, its words and the paths it writes."""

from __future__ import annotations

from pathlib import Path

from utils.shell.paths import ShellState, shell_path, take_assignments
from utils.shell.words import (
    REDIRECTS,
    command_name,
    is_redirection,
    positionals,
    strip_prefixes,
)
from utils.shell.writes import write_targets

CHANGE_DIRECTORY = {"cd", "chdir", "pushd", "set-location", "sl", "push-location"}


def read_segment(
    words: list[str], state: ShellState
) -> tuple[str, list[str], list[str]] | None:
    """Applies a simple command's assignments and cd to the state, so `D=<scratch>; cd "$D" && curl -o x`
    is read the way the shell runs it. Returns the command's name, its words without redirections and
    the paths it writes, or None when it only changes the state."""
    words = strip_prefixes(take_assignments(words, state))
    targets = [
        words[index + 1] for index, word in enumerate(words[:-1]) if word in REDIRECTS
    ]
    words = [
        word for index, word in enumerate(words) if not is_redirection(words, index)
    ]
    if not words:
        return ("", [], targets) if targets else None
    name = command_name(words[0])
    if name in CHANGE_DIRECTORY:
        arguments = positionals(words[1:])
        state.base = shell_path(arguments[0], state) if arguments else Path.home()
        return None
    return name, words, targets + write_targets(name, words[1:])
