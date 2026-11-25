"""Who is calling: a session in neither list is asked where the reviewer is refused; a subagent has
its parent's role; a clone without the role list gives every session the writer's rules."""

from __future__ import annotations

import pytest
from conftest import Answer, Project

# (tool, what the call names, answer)
UNLISTED: list[tuple[str, str, Answer]] = [
    ("Edit", "<project>/chat_bridge/x.py", "ask"),
    ("Workflow", "x", "ask"),
    ("Bash", "rm -rf chat_bridge", "ask"),
    ("Bash", "git status", None),
]

# (parent's role, answer) for a subagent editing code; its transcript sits under its parent's.
SUBAGENTS: list[tuple[str, Answer]] = [("reviewer", "deny"), ("writer", "allow")]

# (tool, what the call names, answer)
CLONE: list[tuple[str, str, Answer]] = [
    ("Edit", "<project>/chat_bridge/x.py", "allow"),
    ("Bash", "git commit -m x", "deny"),
    ("Write", "<home>/notes.txt", "ask"),
    ("Bash", "git status", None),
]


@pytest.mark.parametrize(("tool", "target", "answer"), UNLISTED)
def test_unlisted_session(
    project: Project, tool: str, target: str, answer: Answer
) -> None:
    assert project.ask("unlisted", tool, target) == answer


@pytest.mark.parametrize(("parent", "answer"), SUBAGENTS)
def test_subagent_has_its_parents_role(
    project: Project, parent: str, answer: Answer
) -> None:
    transcript = f"C:/p/<{parent}>/subagents/agent-1.jsonl"
    assert (
        project.ask("subagent", "Edit", "<project>/chat_bridge/x.py", transcript)
        == answer
    )


@pytest.mark.parametrize(("tool", "target", "answer"), CLONE)
def test_clone_without_role_list(
    clone: Project, tool: str, target: str, answer: Answer
) -> None:
    assert clone.ask("anyone", tool, target) == answer
