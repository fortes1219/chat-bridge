"""No chat test starts the user's own Codex: it looks not installed unless a test says otherwise.

With no program named, the service falls back to Codex when Claude Code is not logged in, so a
test that makes Claude Code look missing would otherwise reach the Codex on the machine.

Nor does a chat test start a program to split a question, or read the database for the date the
data reaches, unless it says otherwise: the split lists no parts, and the date is fixed.
"""

from datetime import date

import pytest

from chat_bridge.chat import codex, service
from chat_bridge.chat.split import SplitOutcome

LATEST_EVENT_DATE = date(2026, 11, 17)


@pytest.fixture(autouse=True)
def codex_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> str:
        raise codex.CodexNotFoundError("Codex is not installed")

    monkeypatch.setattr(codex, "find_executable", missing)


@pytest.fixture(autouse=True)
def no_split_and_a_fixed_date(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_parts(program: object, question: str) -> SplitOutcome:
        return SplitOutcome()

    async def latest() -> date:
        return LATEST_EVENT_DATE

    monkeypatch.setattr(service, "split_question", no_parts)
    monkeypatch.setattr(service, "latest_event_date", latest)
