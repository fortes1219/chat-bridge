"""Messages between sessions go through for every role and are logged with their first line, so
the Owner can read who told whom what."""

from __future__ import annotations

from typing import NoReturn

from utils.decision import allow_and_log
from utils.roles import Caller


def log_message(
    caller: Caller, tool_name: str, tool_input: dict[str, object]
) -> NoReturn:
    target = tool_input.get("to", "?")
    first_line = str(tool_input.get("message", "")).strip().splitlines()[:1]
    allow_and_log(
        caller,
        tool_name,
        f"to {target}: {first_line[0][:200] if first_line else '(subscription only)'}",
    )
