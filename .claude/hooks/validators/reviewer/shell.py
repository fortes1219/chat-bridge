"""The reviewer's shell: read each simple command the way the shell runs it, and refuse one that
writes outside the scratch folder or uses what the project built."""

from __future__ import annotations

import re

from utils.roles import Caller
from utils.shell.paths import ShellState
from utils.shell.reading import read_segment
from utils.shell.words import command_segments

from validators.reviewer.commands import (
    INTERPRETERS,
    check_command_use,
    script_argument,
)
from validators.reviewer.git import check_git
from validators.reviewer.refusal import refuse
from validators.reviewer.targets import check_runs, check_targets, looks_like_path
from validators.self_protection import mentions_protected

# Python code that imports the project or runs its tests, inline or in a heredoc. Matched on the
# whole command text, because heredoc bodies are left out of the words.
PROJECT_IMPORT = re.compile(
    r"\bpython.*?(?:-m\s+|\bimport\s+|\bfrom\s+)(?:chat_bridge|pytest)\b",
    re.IGNORECASE | re.DOTALL,
)


def check_shell(caller: Caller, tool_name: str, command: str) -> None:
    if mentions_protected(command):
        refuse(
            caller,
            tool_name,
            "The command mentions the guard or the settings that load it; read them with the Read tool.",
        )
    if PROJECT_IMPORT.search(command):
        refuse(caller, tool_name, "The command runs the project code or its tests.")
    segments = command_segments(command)
    if segments is None:
        refuse(
            caller,
            tool_name,
            "The command could not be read; split it into simpler commands.",
        )
    state = ShellState(caller.cwd, {})
    for words in segments:
        check_segment(caller, tool_name, words, state)


def check_segment(
    caller: Caller, tool_name: str, words: list[str], state: ShellState
) -> None:
    read = read_segment(words, state)
    if read is None:
        return
    name, words, targets = read
    if words:
        check_command_use(caller, tool_name, name, words[1:])
        if name != "." and looks_like_path(words[0]):
            check_runs(caller, tool_name, words[0], state)
        if name in INTERPRETERS:
            script = script_argument(words[1:])
            if script is not None:
                check_runs(caller, tool_name, script, state)
        if name == "git":
            check_git(caller, tool_name, words[1:], state)
    check_targets(caller, tool_name, targets, state)
