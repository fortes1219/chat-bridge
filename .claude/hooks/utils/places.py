"""The folders the guard knows, and where a path sits among them."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

PROJECT_DIR = Path(
    os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3]
).resolve()
INTERNAL_DIR = PROJECT_DIR / ".claude"
DOCS_DIR = INTERNAL_DIR / "docs"
USER_DIR = Path.home() / ".claude"
# This project's memory lives in ~/.claude/projects/<project>/memory/, the folder named after the
# project's path with every character but letters and digits turned into "-". Another project's
# memory is instructions that project's sessions load, so it counts as outside.
USER_PROJECTS_DIR = USER_DIR / "projects"
MEMORY_DIR = (
    USER_PROJECTS_DIR / re.sub(r"[^A-Za-z0-9]", "-", str(PROJECT_DIR)) / "memory"
)
# Every session's scratch folder is under the system temp folder.
TEMP_DIR = Path(tempfile.gettempdir()).resolve()


def is_inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def is_memory(path: Path) -> bool:
    return is_inside(path, MEMORY_DIR)


def is_scratch(path: Path) -> bool:
    """Inside the system temp folder, which holds every session's scratch folder, and not the project."""
    return is_inside(path, TEMP_DIR) and not is_inside(path, PROJECT_DIR)
