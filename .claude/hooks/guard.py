"""PreToolUse guard for the chat-bridge sessions.

Claude Code runs this before a tool call and passes the call as JSON on stdin. The decision is
made by code, not by the model:

  deny  -> the call is refused
  ask   -> the Owner gets a permission prompt showing the call
  allow -> the call goes through without a prompt and is written to the log
  (no output) -> the normal permission flow applies

This file only reads the call, finds who is calling and hands the call to the rules for that
tool. The rules are in validators/, what they share in utils/; README.md draws the tree.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn


def ask_by_hand(reason: str) -> NoReturn:
    """The answer when the guard itself is broken. It needs nothing from the package, so a module
    that fails to load still turns into a prompt, never into a silent pass."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"[chat-bridge guard] {reason}",
            }
        },
        sys.stdout,
    )
    sys.exit(0)


# The package sits next to this file. Python puts this folder on the import path only when it is not
# started isolated (-I) or with PYTHONSAFEPATH, so it is put there by name.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    # Shared: what the guard reads from a call, what it answers, where, and who is calling
    from utils.calls import file_path, shell_command
    from utils.decision import decide
    from utils.places import PROJECT_DIR
    from utils.roles import WRITER, Caller, session_role

    # Rules, one module per use
    from validators import every_role, messages, reviewer, writer
except Exception as error:  # a module that cannot load must not turn into a silent pass
    ask_by_hand(
        f"Guard could not load ({type(error).__name__}: {error}); check it by hand."
    )

ToolCheck = Callable[[Caller, str, dict[str, object]], None]


def check_message(
    caller: Caller, tool_name: str, tool_input: dict[str, object]
) -> None:
    messages.log_message(caller, tool_name, tool_input)


def check_workflow(
    caller: Caller, tool_name: str, tool_input: dict[str, object]
) -> None:
    if caller.role != WRITER:
        reviewer.refuse_workflow(caller, tool_name)


def check_file(caller: Caller, tool_name: str, tool_input: dict[str, object]) -> None:
    rules = writer if caller.role == WRITER else reviewer
    rules.check_file(caller, tool_name, file_path(tool_input))


def check_shell(caller: Caller, tool_name: str, tool_input: dict[str, object]) -> None:
    command = shell_command(tool_input)
    every_role.record(caller, tool_name, command)
    every_role.stop_commits(command)
    rules = writer if caller.role == WRITER else reviewer
    rules.check_shell(caller, tool_name, command)
    every_role.ask_before_uploads(caller, tool_name, command)


# Tools not listed here are left to the normal permission flow.
TOOL_CHECKS: dict[str, ToolCheck] = {
    "SendMessage": check_message,
    # Workflow agents edit code and run the project, and the documentation does not say whether
    # hooks see their tool calls.
    "Workflow": check_workflow,
    "Edit": check_file,
    "Write": check_file,
    "NotebookEdit": check_file,
    "Bash": check_shell,
    "PowerShell": check_shell,
}


def main() -> None:
    # Claude Code sends UTF-8. On Windows, text-mode stdin would decode it with the console code
    # page and fail on any non-ASCII character, so read the bytes and decode them here.
    call = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool_name = str(call.get("tool_name") or "")
    tool_input = call.get("tool_input") or {}
    caller = Caller(
        session_role(call),
        str(call.get("session_id") or ""),
        Path(str(call.get("cwd") or PROJECT_DIR)).resolve(),
    )
    check = TOOL_CHECKS.get(tool_name)
    if check is not None:
        check(caller, tool_name, tool_input)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # a broken guard must not turn into a silent pass
        decide(
            "ask",
            f"Guard could not read this call ({type(error).__name__}); check it by hand.",
        )
