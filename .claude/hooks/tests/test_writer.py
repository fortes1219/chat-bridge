"""The writer: code waits for its spec and Packages table; writes outside the project, its scratch
folder and this project's memory are asked about; so are the guard's own files."""

from __future__ import annotations

import pytest
from conftest import PACKAGES_HEADER, RESEARCH, Answer, Answers, Project, flatten

ANSWERS: Answers = {
    None: [
        ("Write", "<scratch>/x.py"),
        ("Workflow", "x"),
        ("Bash", "uv run pytest"),
        ("Bash", "rm -rf <scratch>/x"),
        ("Bash", "docker compose -f compose.test.yml run --rm slow-tests"),
        ("Write", "<scratch>/x.py"),
        ("Write", "<memory>/x.md"),
        ("Edit", "<project>/.claude/CLAUDE.md"),
        ("Bash", 'S="<scratch>"; for d in a b; do echo x > "$S/$d/out.txt"; done'),
        ("Bash", "echo x > <scratch>/o.txt"),
    ],
    "allow": [
        ("Edit", "<project>/chat_bridge/x.py"),
        ("Edit", "<project>/specs/001-x/spec.md"),
    ],
    "ask": [
        ("Edit", "<project>/.claude/hooks/guard.py"),
        ("Write", "<home>\\.claude\\settings.json"),
        ("Bash", "git add -u"),
        ("Bash", "uv add x"),
        ("Bash", "cat .claude/hooks/guard.py"),
        ("Bash", "rm -rf chat_bridge"),
        ("Edit", "<home>/notes.txt"),
        ("Write", "<home>/other/src/x.ts"),
        ("Write", "<home>/.claude/projects/p/memory/x.md"),
        ("Bash", "echo x > ~/other.txt"),
        ("Bash", "cp a.py <home>/other/a.py"),
        ("Bash", 'cp a.py "$NOPE_UNSET/b.py"'),
    ],
    "deny": [
        ("Bash", "git commit -m x"),
    ],
}


@pytest.mark.parametrize(("answer", "tool", "target"), flatten(ANSWERS))
def test_answer(project: Project, answer: Answer, tool: str, target: str) -> None:
    assert project.ask("writer", tool, target) == answer


# research.md in each shape the spec gate tells apart; None is no research.md at all.
RESEARCH_SHAPES: dict[str, str | None] = {
    "complete": RESEARCH,
    "LGPL license": RESEARCH.replace("| MIT |", "| LGPL-2.1 |"),
    "no research.md": None,
    "no Packages table": "# Research\n\nNo table.\n",
    "a column renamed": RESEARCH.replace("| Size |", "| Bytes |"),
    "a table without rows": f"## Packages\n\n{PACKAGES_HEADER}\n",
    "package none": RESEARCH.replace("| pdf-inspector |", "| none |"),
    "GPL license": RESEARCH.replace("| MIT |", "| GPL-3.0 |"),
    "AGPL license": RESEARCH.replace("| MIT |", "| AGPL-3.0 |"),
    "a citation without a commit": RESEARCH.replace("@2373cc7:", ":"),
    "an empty size": RESEARCH.replace("| 6.2 MB wheel |", "|  |"),
    "an open NEEDS CLARIFICATION": RESEARCH + "\n[NEEDS CLARIFICATION: chunking]\n",
}

# (research.md shape, tool, what the call names, answer)
GATE: list[tuple[str, str, str, Answer]] = [
    ("complete", "Edit", "<project>/chat_bridge/x.py", "allow"),
    ("complete", "Bash", "sed -i 's/a/b/' chat_bridge/x.py", None),
    ("LGPL license", "Edit", "<project>/chat_bridge/x.py", "allow"),
    ("no research.md", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("no Packages table", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("a column renamed", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("a table without rows", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("package none", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("GPL license", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("AGPL license", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("a citation without a commit", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("an empty size", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("an open NEEDS CLARIFICATION", "Edit", "<project>/chat_bridge/x.py", "deny"),
    ("no research.md", "Bash", "sed -i 's/a/b/' chat_bridge/x.py", "deny"),
    ("no research.md", "Bash", "echo x > README.md", "deny"),
    (
        "no research.md",
        "PowerShell",
        "Set-Content -Path chat_bridge\\x.py -Value 'x'",
        "deny",
    ),
    (
        "no research.md",
        "Bash",
        "echo x > specs/001-x/notes.md && echo y > .claude/docs/a.md",
        None,
    ),
    (
        "no research.md",
        "Bash",
        "cp chat_bridge/x.py <scratch>/ && uv run pytest > <scratch>/out.txt",
        None,
    ),
    ("no research.md", "Edit", "<project>/specs/001-x/research.md", "allow"),
]


@pytest.mark.parametrize(("variant", "tool", "target", "answer"), GATE)
def test_spec_gate(
    project: Project, variant: str, tool: str, target: str, answer: Answer
) -> None:
    project.write_research(RESEARCH_SHAPES[variant])
    try:
        assert project.ask("writer", tool, target) == answer
    finally:
        project.write_research(RESEARCH)
