"""Building and serving the chat page, without the machine's own Node.js or npm."""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge import web
from chat_bridge.chat import service
from chat_bridge.chat.programs import Login, Program
from chat_bridge.chat.schemas import ProgramState
from chat_bridge.chat.server import create_app
from chat_bridge.errors import LocalSetupError

PAGE = "<!doctype html><title>chat</title>"


class FakeNode:
    """Stands in for `node` and `npm`: records each run, and a build writes a page."""

    def __init__(self, version: str = "v24.22.3", build_exit: int = 0) -> None:
        self.version = version
        self.build_exit = build_exit
        self.runs: list[list[str]] = []

    def run(
        self, args: list[str], cwd: Path | None = None, **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        command = [Path(args[0]).name, *args[1:]]
        self.runs.append(command)
        if command == ["node", "--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=self.version + "\n")
        if command == ["npm", "run", "build"] and cwd is not None:
            if self.build_exit:
                return subprocess.CompletedProcess(args, self.build_exit)
            (cwd / "dist" / "assets").mkdir(parents=True, exist_ok=True)
            (cwd / "dist" / "index.html").write_text(PAGE, encoding="utf-8")
        return subprocess.CompletedProcess(args, 0)


@pytest.fixture
def frontend(tmp_path: Path) -> Path:
    folder = tmp_path / "frontend"
    (folder / "src").mkdir(parents=True)
    (folder / "package.json").write_text("{}", encoding="utf-8")
    (folder / "src" / "main.ts").write_text("export {}", encoding="utf-8")
    return folder


def _use(
    monkeypatch: pytest.MonkeyPatch,
    fake: FakeNode,
    found: tuple[str, ...] = ("node", "npm"),
) -> None:
    monkeypatch.setattr(
        shutil, "which", lambda name: f"/bin/{name}" if name in found else None
    )
    monkeypatch.setattr(subprocess, "run", fake.run)


# --- Node.js missing or too old ---------------------------------------------------------


@pytest.mark.parametrize("missing", ["node", "npm"])
def test_a_missing_node_or_npm_is_named_with_the_version_to_install(
    frontend: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    fake = FakeNode()
    _use(monkeypatch, fake, found=tuple({"node", "npm"} - {missing}))

    with pytest.raises(LocalSetupError, match=f"`{missing}` was not found") as raised:
        web.prepare_page(frontend)

    assert "24.22.3" in str(raised.value)
    assert ["npm", "ci"] not in fake.runs


@pytest.mark.parametrize(
    ("reported", "named"),
    [
        ("v24.16.0", "Install Node.js 24.22.3 or later"),
        ("v22.23.4", "Install Node.js 22.23.5 or later"),
        ("v20.19.5", "no longer gets security fixes"),
        ("v25.9.0", "no longer gets security fixes"),
        ("not a version", "Could not read the Node.js version"),
    ],
)
def test_an_old_node_is_refused_by_name_and_nothing_is_installed(
    frontend: Path, monkeypatch: pytest.MonkeyPatch, reported: str, named: str
) -> None:
    fake = FakeNode(version=reported)
    _use(monkeypatch, fake)

    with pytest.raises(LocalSetupError, match=named):
        web.prepare_page(frontend)

    assert fake.runs == [["node", "--version"]]


@pytest.mark.parametrize(
    "reported", ["v22.23.5", "v24.22.3", "v24.30.0", "v26.13.1", "v28.0.0"]
)
def test_a_supported_line_at_its_security_release_or_a_newer_line_builds(
    frontend: Path, monkeypatch: pytest.MonkeyPatch, reported: str
) -> None:
    _use(monkeypatch, FakeNode(version=reported))

    assert web.prepare_page(frontend) == frontend / "dist"


def test_a_node_in_the_folder_the_service_runs_from_is_not_run(
    frontend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeNode()
    _use(monkeypatch, fake)
    planted = str(Path.cwd() / "node.cmd")
    monkeypatch.setattr(shutil, "which", lambda name: planted)

    with pytest.raises(LocalSetupError, match="folder the service runs from"):
        web.prepare_page(frontend)

    assert fake.runs == []


# --- Building only when needed ----------------------------------------------------------


def test_the_page_is_built_once_and_again_only_after_a_source_changes(
    frontend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeNode()
    _use(monkeypatch, fake)
    build = [["node", "--version"], ["npm", "ci"], ["npm", "run", "build"]]

    web.prepare_page(frontend)
    assert fake.runs == build

    fake.runs.clear()
    web.prepare_page(frontend)
    assert fake.runs == []

    (frontend / "src" / "main.ts").write_text(
        "export const changed = 1", encoding="utf-8"
    )
    web.prepare_page(frontend)
    assert fake.runs == build


def test_installed_packages_and_the_build_are_not_sources(
    frontend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeNode()
    _use(monkeypatch, fake)
    web.prepare_page(frontend)
    (frontend / "node_modules" / "vue").mkdir(parents=True)
    (frontend / "node_modules" / "vue" / "index.js").write_text("1", encoding="utf-8")
    (frontend / "dist" / "extra.txt").write_text("1", encoding="utf-8")

    fake.runs.clear()
    web.prepare_page(frontend)

    assert fake.runs == []


def test_a_failed_build_is_reported_and_done_again_on_the_next_run(
    frontend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, FakeNode(build_exit=1))
    with pytest.raises(
        LocalSetupError, match="`npm run build` failed with exit code 1"
    ):
        web.prepare_page(frontend)

    fake = FakeNode()
    _use(monkeypatch, fake)
    web.prepare_page(frontend)

    assert ["npm", "run", "build"] in fake.runs


def test_a_missing_source_folder_is_named(tmp_path: Path) -> None:
    with pytest.raises(LocalSetupError, match="source is missing"):
        web.prepare_page(tmp_path / "frontend")


# --- Serving ----------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(PAGE, encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "favicon.ico").write_bytes(b"\0icon")
    (tmp_path / "secret.txt").write_text("outside the build", encoding="utf-8")

    async def states() -> list[ProgramState]:
        return [ProgramState(program=Program.CODEX, state=Login.LOGGED_IN)]

    monkeypatch.setattr(service, "program_states", states)
    with TestClient(create_app(page=dist), base_url="http://127.0.0.1") as test_client:
        yield test_client


@pytest.mark.parametrize("address", ["/", "/?lang=en&program=codex", "/strategy"])
def test_the_page_and_any_address_it_owns_return_index_html(
    client: TestClient, address: str
) -> None:
    response = client.get(address)

    assert response.status_code == 200
    assert response.text == PAGE


def test_files_of_the_build_are_sent_as_they_are(client: TestClient) -> None:
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/favicon.ico").content == b"\0icon"
    assert client.get("/assets/missing.js").status_code == 404


def test_the_service_still_answers_and_its_unknown_paths_are_404(
    client: TestClient,
) -> None:
    response = client.get("/chat/programs")

    assert response.status_code == 200
    assert response.json()[0]["program"] == "codex"
    assert client.get("/chat/nothing-here").status_code == 404


# Each reaches the route as a path that leads to secret.txt, next to the build.
@pytest.mark.parametrize(
    "address", ["/..%2fsecret.txt", "/a%2f..%2f..%2fsecret.txt", "/%2e%2e%5csecret.txt"]
)
def test_a_path_out_of_the_build_gets_the_page_not_the_file(
    client: TestClient, address: str
) -> None:
    response = client.get(address)

    assert response.text == PAGE
