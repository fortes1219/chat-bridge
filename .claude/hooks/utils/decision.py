"""What the guard answers Claude Code, and the log of what it let through or stopped.

Frequent calls (messages between sessions, file edits) are let through and logged to
.claude/guard.log with the role, so the Owner can read them back without being prompted.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import NoReturn

from utils.places import INTERNAL_DIR
from utils.roles import Caller

LOG_PATH = INTERNAL_DIR / "guard.log"


def log(caller: Caller, tool_name: str, detail: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8", errors="replace", newline="\n") as handle:
        handle.write(f"{stamp}\t{caller.tag}\t{tool_name}\t{detail}\n")


def decide(decision: str, reason: str) -> NoReturn:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": f"[chat-bridge guard] {reason}",
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def allow_and_log(caller: Caller, tool_name: str, detail: str) -> NoReturn:
    log(caller, tool_name, detail)
    decide("allow", f"Logged to .claude/guard.log: {detail}")


def ask_and_log(caller: Caller, tool_name: str, reason: str) -> NoReturn:
    log(caller, tool_name, f"ASKED: {reason}")
    decide("ask", reason)
