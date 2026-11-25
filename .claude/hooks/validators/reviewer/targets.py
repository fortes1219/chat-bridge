"""Where the reviewer's shell may write and what it may run: writes only to its scratch folder, its
memory and the internal documents; runs nothing from the project."""

from __future__ import annotations

from utils.places import DOCS_DIR, PROJECT_DIR, is_inside, is_memory, is_scratch
from utils.roles import Caller
from utils.shell.paths import ShellState, shell_path
from utils.shell.writes import DISCARD

from validators.reviewer.refusal import refuse


def check_targets(
    caller: Caller, tool_name: str, targets: list[str], state: ShellState
) -> None:
    for target in targets:
        if target.lower() in DISCARD:
            continue
        path = shell_path(target, state)
        if path is None:
            refuse(
                caller,
                tool_name,
                f"The command writes to {target}, which this guard cannot resolve; name a path in the scratch folder.",
            )
        if is_inside(path, DOCS_DIR) or is_memory(path) or is_scratch(path):
            continue
        if is_inside(path, PROJECT_DIR):
            refuse(
                caller,
                tool_name,
                f"The command writes to {path.relative_to(PROJECT_DIR).as_posix() or '.'} in the project.",
            )
        refuse(
            caller,
            tool_name,
            f"The command writes to {path}, outside the scratch folder.",
        )


def check_runs(caller: Caller, tool_name: str, word: str, state: ShellState) -> None:
    path = shell_path(word, state)
    if path is None:
        refuse(
            caller,
            tool_name,
            f"The command runs {word}, which this guard cannot resolve.",
        )
    if is_inside(path, PROJECT_DIR):
        refuse(caller, tool_name, f"The command runs {word}, a file from the project.")


def looks_like_path(word: str) -> bool:
    return "/" in word or "\\" in word or word.startswith(".")
