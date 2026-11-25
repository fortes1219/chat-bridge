"""The writer's rules: repository files wait for the spec gate, by file tool or by shell; writing
outside the project, the scratch folder and the session memory is asked about; the Owner is also
prompted for installs, repository state changes, deleting folders and changes to the guard."""

from __future__ import annotations

import re
from pathlib import Path

from utils.decision import allow_and_log, ask_and_log, decide, log
from utils.places import INTERNAL_DIR, PROJECT_DIR, is_inside, is_memory, is_scratch
from utils.roles import Caller
from utils.shell.paths import ShellState, known_folder, shell_path
from utils.shell.reading import read_segment
from utils.shell.words import command_segments
from utils.shell.writes import DISCARD

from validators import every_role
from validators.self_protection import (
    PROTECTED_REASON,
    is_protected,
    mentions_protected,
)
from validators.spec_gate import (
    SPECIFY_DIR,
    SPECS_DIR,
    is_spec_artifact,
    repository_refusal,
)

DELETE_FOLDER = re.compile(
    r"(\brm\s+-[a-zA-Z]*r|\bRemove-Item\b[^|;\n]*-Recurse|\brmdir\s+/s|\bdel\s+/s)"
)
# Every session's scratch folder has this in its path; deleting a folder there needs no prompt.
SCRATCH_MARKER = "/temp/claude/"
OUTSIDE = "outside the project, the scratch folder and the session memory"


def check_file(caller: Caller, tool_name: str, path: Path) -> None:
    if is_protected(path):
        decide("ask", f"{PROTECTED_REASON}: {path}")
    if is_scratch(path) or is_memory(path):
        return
    if not is_inside(path, PROJECT_DIR):
        ask_and_log(caller, tool_name, f"Writes {path}, {OUTSIDE}.")
    if is_inside(path, INTERNAL_DIR):
        # Internal notes, the project instructions and the skills: no spec gate, but on record.
        log(
            caller,
            tool_name,
            f"internal file {path.relative_to(PROJECT_DIR).as_posix()}",
        )
        return
    check_repository_file(caller, tool_name, path)


def check_repository_file(caller: Caller, tool_name: str, path: Path) -> None:
    relative_path = path.relative_to(PROJECT_DIR).as_posix()
    if is_spec_artifact(path):
        allow_and_log(caller, tool_name, f"spec artifact {relative_path}")
    refusal = repository_refusal(relative_path)
    if refusal is not None:
        log(caller, tool_name, f"BLOCKED: {refusal}")
        decide("deny", refusal)
    allow_and_log(caller, tool_name, f"repository file {relative_path}")


def check_shell(caller: Caller, tool_name: str, command: str) -> None:
    if (
        DELETE_FOLDER.search(command)
        and SCRATCH_MARKER not in command.replace("\\", "/").lower()
    ):
        decide("ask", "Deletes a folder outside the session scratch area.")
    every_role.ask_before_changes(command)
    if mentions_protected(command):
        decide("ask", "The command mentions the guard or the settings that load it.")
    check_shell_writes(caller, tool_name, command)


def check_shell_writes(caller: Caller, tool_name: str, command: str) -> None:
    """The paths a shell command writes pass the same checks as the file tools. A repository file
    that waits for its spec is refused before anything is asked. A command the guard cannot read
    is only logged, and programs that write files themselves are not seen."""
    segments = command_segments(command)
    if segments is None:
        return
    state = ShellState(caller.cwd, {})
    outside: str | None = None
    for words in segments:
        read = read_segment(words, state)
        if read is None:
            continue
        for target in read[2]:
            if target.lower() in DISCARD:
                continue
            path = shell_path(target, state)
            if path is None:
                folder = known_folder(target, state)
                if folder is not None and (is_scratch(folder) or is_memory(folder)):
                    continue
                outside = (
                    outside
                    or f"The command writes to {target}, which the guard cannot resolve."
                )
                continue
            if is_scratch(path) or is_memory(path):
                continue
            if not is_inside(path, PROJECT_DIR):
                outside = outside or f"The command writes to {path}, {OUTSIDE}."
                continue
            if any(
                is_inside(path, folder)
                for folder in (INTERNAL_DIR, SPECIFY_DIR, SPECS_DIR)
            ):
                continue
            refusal = repository_refusal(
                path.relative_to(PROJECT_DIR).as_posix() or "."
            )
            if refusal is not None:
                log(caller, tool_name, f"BLOCKED: {refusal}")
                decide("deny", refusal)
    if outside is not None:
        ask_and_log(caller, tool_name, outside)
