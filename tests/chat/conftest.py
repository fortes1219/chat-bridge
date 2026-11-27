"""No chat test starts the user's own Codex: it looks not installed unless a test says otherwise.

With no program named, the service falls back to Codex when Claude Code is not logged in, so a
test that makes Claude Code look missing would otherwise reach the Codex on the machine.

Nor does a chat test start a program to split a question, or read the database for the date the
data reaches, for the market sections of the documents found or for the profile, unless it says
otherwise: the split lists no parts, the date is fixed, no document has a market section, and
there is no profile.
"""

import asyncio
import sys
from asyncio.subprocess import Process
from collections.abc import Awaitable, Callable
from datetime import date
from pathlib import Path

import psutil
import pytest

from chat_bridge.chat import codex, service
from chat_bridge.chat.split import SplitOutcome

LATEST_EVENT_DATE = date(2026, 11, 17)
# The program below the launcher says it is running, so a test lists the processes only once
# all of them exist. It then waits long enough that only a kill ends it.
WAITING_PROGRAM = "import time; print('ready', flush=True); time.sleep(60)"
READY_TIMEOUT_SECONDS = 10

StartProgram = Callable[..., Awaitable[Process]]
StartLauncher = Callable[
    [StartProgram], Awaitable[tuple[Process, list[psutil.Process]]]
]


@pytest.fixture(autouse=True)
def codex_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> str:
        raise codex.CodexNotFoundError("Codex is not installed")

    monkeypatch.setattr(codex, "find_executable", missing)


@pytest.fixture(autouse=True)
def no_split_and_a_fixed_date(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_parts(
        program: object,
        question: str,
        holdings: object = None,
        *,
        effort: object = None,
    ) -> SplitOutcome:
        return SplitOutcome()

    async def latest() -> date:
        return LATEST_EVENT_DATE

    async def no_market_sections(section_ids: object, heading: str) -> list[object]:
        return []

    monkeypatch.setattr(service, "split_question", no_parts)
    monkeypatch.setattr(service, "latest_event_date", latest)
    monkeypatch.setattr(service, "sections_headed", no_market_sections)


@pytest.fixture(autouse=True)
def no_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    # Apart from the one above: the strategy tests share that one and read their own profile.
    async def none() -> None:
        return None

    monkeypatch.setattr(service, "_profile_or_none", none)


@pytest.fixture
def empty_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """A PATH and a current folder that hold no program, as a service has that was started
    before a program was installed. Returns a folder, not yet made, to install into."""
    on_path = tmp_path / "on-path"
    on_path.mkdir()
    monkeypatch.setenv("PATH", str(on_path))
    monkeypatch.chdir(on_path)
    return tmp_path / "installed"


def install(folder: Path, name: str) -> Path:
    """A stand-in for a program an installer left in `folder`, under the name the system gives
    it: `name.exe` on Windows, an executable file `name` elsewhere."""
    folder.mkdir(parents=True, exist_ok=True)
    program = folder / (f"{name}.exe" if sys.platform == "win32" else name)
    program.write_text("", encoding="utf-8")
    program.chmod(0o755)
    return program


@pytest.fixture
def start_launcher(tmp_path: Path) -> StartLauncher:
    """Starts, with a program's own start function, a stand-in for what npm installs on Windows.

    npm installs Claude Code and Codex as a `.cmd` launcher: cmd.exe starts node, which starts
    the program, and the program holds the output pipes. Here cmd.exe starts Python, which
    starts the interpreter that waits. Killing cmd.exe alone leaves both running. Returns the
    started process and every process below it.
    """
    launcher = tmp_path / "program.cmd"
    launcher.write_text(
        f'@"{sys.executable}" -c "{WAITING_PROGRAM}"\r\n', encoding="utf-8"
    )

    async def start(
        start_program: StartProgram,
    ) -> tuple[Process, list[psutil.Process]]:
        process = await start_program([str(launcher)], with_input=True)
        assert process.stdout is not None
        await asyncio.wait_for(process.stdout.readline(), READY_TIMEOUT_SECONDS)
        return process, psutil.Process(process.pid).children(recursive=True)

    return start
