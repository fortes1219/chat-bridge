"""No chat test starts the user's own Codex: it looks not installed unless a test says otherwise.

With no program named, the service falls back to Codex when Claude Code is not logged in, so a
test that makes Claude Code look missing would otherwise reach the Codex on the machine.
"""

import pytest

from chat_bridge.chat import codex


@pytest.fixture(autouse=True)
def codex_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> str:
        raise codex.CodexError("Codex is not installed")

    monkeypatch.setattr(codex, "find_executable", missing)
