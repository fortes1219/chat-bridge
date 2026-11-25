"""How the reviewer's limits say no: the reviewer is denied; a session in neither role list is asked
about, so the Owner sees what it tried and decides. Both are logged."""

from __future__ import annotations

from typing import NoReturn

from utils.decision import decide, log
from utils.roles import REVIEWER, Caller

REVIEWER_SCOPE = (
    "The reviewer may only look up the ecosystem, update the internal documents in "
    ".claude/docs/, take stock of progress, run shell commands that read, and run the "
    "checks: `uv run --no-sync pytest|ruff|mypy`, `uv lock --check`, and "
    "`docker compose -f compose.test.yml run --rm [-T] slow-tests [pytest arguments]`."
)


def refuse(caller: Caller, tool_name: str, reason: str) -> NoReturn:
    if caller.role == REVIEWER:
        log(caller, tool_name, f"DENIED: {reason}")
        decide("deny", f"{reason} {REVIEWER_SCOPE}")
    log(caller, tool_name, f"ASKED: {reason}")
    decide(
        "ask",
        f"This session ({caller.session[:8] or '?'}) is not listed in .claude/hooks/roles.json, "
        f"so it has the reviewer's limits. {reason}",
    )


def refuse_workflow(caller: Caller, tool_name: str) -> NoReturn:
    refuse(caller, tool_name, "Workflow agents edit code and run the project.")
