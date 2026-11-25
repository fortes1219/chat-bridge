"""The parts of a tool call the rules read: the file a file tool changes, the command a shell runs.
A call without them is asked about, never let through."""

from __future__ import annotations

from pathlib import Path

from utils.decision import decide
from utils.places import PROJECT_DIR


def file_path(tool_input: dict[str, object]) -> Path:
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        decide("ask", "File tool call without a readable path.")
    path = Path(raw)
    return (path if path.is_absolute() else PROJECT_DIR / path).resolve()


def shell_command(tool_input: dict[str, object]) -> str:
    command = tool_input.get("command")
    if not isinstance(command, str):
        decide("ask", "Shell call without a readable command.")
    return command
