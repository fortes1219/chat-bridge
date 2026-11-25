"""The reviewer's file tools: only the internal documents, its scratch folder and its memory."""

from __future__ import annotations

from pathlib import Path

from utils.decision import allow_and_log
from utils.places import DOCS_DIR, PROJECT_DIR, is_inside, is_memory, is_scratch
from utils.roles import Caller

from validators.reviewer.refusal import refuse
from validators.self_protection import PROTECTED_REASON, is_protected


def check_file(caller: Caller, tool_name: str, path: Path) -> None:
    if is_protected(path):
        refuse(caller, tool_name, f"{PROTECTED_REASON}: {path}")
    if is_inside(path, DOCS_DIR):
        allow_and_log(
            caller,
            tool_name,
            f"internal document {path.relative_to(PROJECT_DIR).as_posix()}",
        )
    if is_inside(path, PROJECT_DIR):
        refuse(
            caller,
            tool_name,
            f"{path.relative_to(PROJECT_DIR).as_posix()} is a project file outside .claude/docs/.",
        )
    if is_scratch(path) or is_memory(path):
        return  # its own scratch folder and memory
    refuse(
        caller,
        tool_name,
        f"{path} is outside the scratch folder and the session memory folder.",
    )
