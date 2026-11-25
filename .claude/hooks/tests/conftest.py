"""A throwaway project with this guard installed, and a way to ask it about one call.

The project sits in pytest's temporary folder. The stand-in for a session's scratch folder is made
under <system temp>/claude/, where Claude Code puts the real ones and where the guard lets a
session delete folders; it is removed afterwards.
Cases name places with tokens (<project>, <scratch>, <home>, <memory>, <slug>) and sessions with
roles, so they hold no machine's paths and no real session ids.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
SESSIONS = {
    "writer": "aaaaaaaa-1111-2222-3333-444444444444",
    "reviewer": "bbbbbbbb-1111-2222-3333-444444444444",
    "unlisted": "cccccccc-1111-2222-3333-444444444444",
}
FEATURE = "specs/001-x"
PACKAGES_HEADER = (
    "| Need | Package | Version | License | Size | Dependency declared in | Called in |\n"
    "|---|---|---|---|---|---|---|\n"
)
PACKAGE_ROW = (
    "| Read PDF | pdf-inspector | 1.27.0 | MIT | 6.2 MB wheel "
    "| `zylon-ai/private-gpt@2373cc7:pyproject.toml:120-123` "
    "| `zylon-ai/private-gpt@2373cc7b9:private_gpt/components/readers/pdf_inspector/pdf_inspector_reader.py:42` |\n"
)
RESEARCH = f"# Research\n\nIntro.\n\n## Packages\n\n{PACKAGES_HEADER}{PACKAGE_ROW}\n## Decisions\n\nText.\n"

# Where each tool carries what it names.
INPUT_KEYS = {
    "Bash": "command",
    "PowerShell": "command",
    "Edit": "file_path",
    "Write": "file_path",
    "NotebookEdit": "notebook_path",
    "Workflow": "script",
    "SendMessage": "message",
}

# The guard's answers: None leaves the call to the normal permission flow, "allow" lets it through
# and logs it, "ask" prompts the person at the keyboard, "deny" refuses it.
Answer = str | None
# Each answer with the calls, (tool, what the call names), that get it.
Answers = dict[Answer, list[tuple[str, str]]]


def tool_input(tool: str, target: str) -> dict[str, object]:
    extra: dict[str, object] = {"to": "peer"} if tool == "SendMessage" else {}
    return {INPUT_KEYS[tool]: target, **extra}


def flatten(answers: Answers) -> list[tuple[Answer, str, str]]:
    return [
        (answer, tool, target)
        for answer, calls in answers.items()
        for tool, target in calls
    ]


@dataclass(frozen=True)
class Project:
    root: Path
    scratch: Path

    @property
    def slug(self) -> str:
        # Claude Code names a project's folder after its path, every character but letters and
        # digits turned into "-"; the guard finds the project's memory the same way.
        return re.sub(r"[^A-Za-z0-9]", "-", str(self.root))

    def place(self, text: str) -> str:
        memory = Path.home() / ".claude" / "projects" / self.slug / "memory"
        for token, value in (
            ("<memory>", memory.as_posix()),
            ("<slug>", self.slug),
            ("<project>", self.root.as_posix()),
            ("<scratch>", self.scratch.as_posix()),
            ("<home>", Path.home().as_posix()),
            *((f"<{role}>", session) for role, session in SESSIONS.items()),
        ):
            text = text.replace(token, value)
        return text

    def ask(
        self, session: str, tool: str, target: str, transcript: str = ""
    ) -> str | None:
        """The guard's decision for one call, or None when it leaves the call alone.

        `target` is what the call names: the command of a shell call, the path of a file call.
        """
        session_id = SESSIONS.get(session, session)
        call = {
            "session_id": session_id,
            "transcript_path": self.place(transcript) or f"C:/x/{session_id}.jsonl",
            "cwd": str(self.root),
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": tool_input(tool, self.place(target)),
        }
        done = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(self.root / ".claude" / "hooks" / "guard.py"),
            ],
            input=json.dumps(call).encode("utf-8"),
            capture_output=True,
            env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root)),
            timeout=60,
            check=True,
        )
        answer = done.stdout.decode("utf-8").strip()
        if not answer:
            return None
        decision = json.loads(answer)["hookSpecificOutput"]["permissionDecision"]
        assert isinstance(decision, str)
        return decision

    def write_research(self, text: str | None) -> None:
        path = self.root / FEATURE / "research.md"
        if text is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(text, encoding="utf-8")

    def log(self) -> list[str]:
        path = self.root / ".claude" / "guard.log"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def build(root: Path, scratch: Path, *, roles: bool) -> Project:
    hooks = root / ".claude" / "hooks"
    for folder in (".claude/docs/extra", ".specify", FEATURE, "chat_bridge", "scripts"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        HOOKS,
        hooks,
        ignore=shutil.ignore_patterns(
            "__pycache__", "tests", "roles.json", "README.md"
        ),
    )
    if roles:
        listed = {"writer": [SESSIONS["writer"]], "reviewer": [SESSIONS["reviewer"]]}
        (hooks / "roles.json").write_text(json.dumps(listed), encoding="utf-8")
    (root / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": FEATURE}), encoding="utf-8"
    )
    for name in ("spec.md", "plan.md", "tasks.md"):
        (root / FEATURE / name).write_text("# done\n", encoding="utf-8")
    project = Project(root.resolve(), scratch.resolve())
    project.write_research(RESEARCH)
    return project


@pytest.fixture(scope="module")
def scratch() -> Iterator[Path]:
    folder = Path(tempfile.mkdtemp(prefix="guard-tests-", dir=claude_temp()))
    yield folder
    shutil.rmtree(folder, ignore_errors=True)


def claude_temp() -> Path:
    folder = Path(tempfile.gettempdir()) / "claude"
    folder.mkdir(exist_ok=True)
    return folder


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory, scratch: Path) -> Project:
    """A project with a role list, as on the maintainer's machine."""
    return build(tmp_path_factory.mktemp("project"), scratch, roles=True)


@pytest.fixture(scope="module")
def clone(tmp_path_factory: pytest.TempPathFactory, scratch: Path) -> Project:
    """A project without a role list, as after a clone."""
    return build(tmp_path_factory.mktemp("clone"), scratch, roles=False)
