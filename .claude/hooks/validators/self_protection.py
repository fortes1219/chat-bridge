"""The guard protects itself: its own files, the role list and the settings that load it.

The user's settings count too: one setting there turns every hook off.
"""

from __future__ import annotations

import re
from pathlib import Path

from utils.places import INTERNAL_DIR, USER_DIR, is_inside

PROTECTED = (
    INTERNAL_DIR / "hooks",
    INTERNAL_DIR / "settings.json",
    INTERNAL_DIR / "settings.local.json",
    USER_DIR / "settings.json",
    USER_DIR / "settings.local.json",
)
PROTECTED_IN_COMMAND = re.compile(r"\.claude[\\/](hooks|settings(\.local)?\.json)")
PROTECTED_REASON = "Changes the guard, the role list or the settings that load it"


def is_protected(path: Path) -> bool:
    return any(is_inside(path, protected) for protected in PROTECTED)


def mentions_protected(command: str) -> bool:
    return PROTECTED_IN_COMMAND.search(command) is not None
