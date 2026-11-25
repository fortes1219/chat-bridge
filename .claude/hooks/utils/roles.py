"""Who is calling: the writer, the reviewer, or a session in neither list.

.claude/hooks/roles.json lists the session ids of each role. The hook input carries the session id,
and a subagent's transcript sits under its parent's session folder, so a subagent has its parent's
role.

The list is private (session ids), so a clone has none. Without it every session is the writer:
code still waits for its spec, and commits, installs and writes outside the project still stop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.places import INTERNAL_DIR

ROLES_PATH = INTERNAL_DIR / "hooks" / "roles.json"
WRITER = "writer"
REVIEWER = "reviewer"
UNLISTED = "unlisted"


@dataclass(frozen=True)
class Caller:
    role: str
    session: str
    cwd: Path

    @property
    def tag(self) -> str:
        return f"{self.role}:{self.session[:8] or '?'}"


def session_role(call: dict[str, object]) -> str:
    if not ROLES_PATH.exists():
        return WRITER
    roles = json.loads(ROLES_PATH.read_text(encoding="utf-8-sig"))
    if not isinstance(roles, dict):
        raise ValueError("roles.json is not an object")
    session = str(call.get("session_id") or "")
    transcript = str(call.get("transcript_path") or "")
    for role in (WRITER, REVIEWER):
        ids = roles.get(role, [])
        if not isinstance(ids, list) or not all(
            isinstance(item, str) and item for item in ids
        ):
            raise ValueError(f'roles.json: "{role}" is not a list of session ids')
        if any(item == session or item in transcript for item in ids):
            return role
    return UNLISTED
