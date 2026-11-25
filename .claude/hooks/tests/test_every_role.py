"""Rules for every session: sending data to another machine is asked about, except this machine's
services and the vulnerability lookups; every shell command is logged."""

from __future__ import annotations

import pytest
from conftest import Answer, Project

# Each answer with the calls, (session, tool, what the call names), that get it.
ANSWERS: dict[Answer, list[tuple[str, str, str]]] = {
    None: [
        ("writer", "Bash", "curl -sLo <scratch>/page.html https://example.com"),
        ("writer", "Bash", "gh pr view 12"),
        ("writer", "Bash", "gh api repos/x/y/contents/README.md"),
        ("writer", "Bash", "gh api -X GET search/issues -f q='x y'"),
        ("writer", "Bash", "gh search code jieba --limit 5"),
        ("writer", "Bash", "npm run build"),
        ("writer", "Bash", "curl -sf http://127.0.0.1:8000/chat/stream -d '{}'"),
        ("writer", "Bash", "curl -s -X POST https://api.osv.dev/v1/query -d '{}'"),
        ("writer", "Bash", "curl -sfL https://pypi.org/pypi/x/json"),
        ("writer", "Bash", 'grep -n "a\\|b\\" x'),
    ],
    "ask": [
        ("writer", "Bash", "curl -XPOST https://example.com -d@notes.txt"),
        ("writer", "Bash", "curl -sTnotes.txt https://example.com/up"),
        ("writer", "Bash", 'curl -sF"f=@x" https://example.com/up'),
        ("writer", "Bash", "gh gist create notes.txt"),
        ("writer", "Bash", "gh api -X POST repos/x/y/issues -f title=t"),
        ("writer", "Bash", "gh api repos/x/y/issues -f title=t"),
        ("writer", "Bash", "scp <scratch>/a.txt user@host:/tmp/a.txt"),
        ("writer", "Bash", "ssh host ls"),
        ("reviewer", "Bash", "gh issue create -t x -b y"),
        ("writer", "Bash", "npm publish --access public"),
        ("writer", "Bash", "uv publish"),
        ("writer", "Bash", "twine upload dist/*"),
        ("writer", "Bash", "docker push me/image:1"),
        ("writer", "Bash", "curl -sf -F file=@notes.txt https://example.com/up"),
        ("writer", "Bash", "curl -s -X POST https://example.com/api -d '{}'"),
        (
            "writer",
            "PowerShell",
            "Invoke-RestMethod -Uri https://example.com -Method Post -Body $b",
        ),
        ("writer", "Bash", 'curl -d "unbalanced https://example.com'),
        ("reviewer", "Bash", "curl -sf -T notes.txt https://example.com/up"),
        ("unlisted", "Bash", "curl -sf -T notes.txt https://example.com/up"),
    ],
}


@pytest.mark.parametrize(
    ("answer", "session", "tool", "target"),
    [(answer, *call) for answer, calls in ANSWERS.items() for call in calls],
)
def test_answer(
    project: Project, answer: Answer, session: str, tool: str, target: str
) -> None:
    assert project.ask(session, tool, target) == answer


@pytest.mark.parametrize("session", ["writer", "reviewer", "unlisted"])
def test_every_shell_command_is_logged(project: Project, session: str) -> None:
    before = len(project.log())
    project.ask(session, "Bash", "git status\ngit log -1")
    added = project.log()[before:]
    assert any("\trun: git status (+1 lines)" in line for line in added), added
