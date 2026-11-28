"""What `uv run chat-bridge` does before the service runs: the port, the browser, the message."""

import socket
import threading
import webbrowser
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
import uvicorn

from chat_bridge import cli, web
from chat_bridge.chat import server
from chat_bridge.database import SchemaMismatchError
from chat_bridge.ingest import service as ingest_service


@pytest.fixture
def started(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[dict[str, list[object]]]:
    """Records what serve() opens and runs, without building, binding or opening anything."""
    calls: dict[str, list[object]] = {
        "browser": [],
        "uvicorn": [],
        "waiter": [],
        "prepared": [],
    }
    (tmp_path / "assets").mkdir()

    def prepare_page() -> Path:
        calls["prepared"].append("page")
        return tmp_path

    monkeypatch.setattr(web, "prepare_page", prepare_page)
    monkeypatch.setattr(
        server,
        "prepare_knowledge_base",
        lambda: calls["prepared"].append("knowledge base"),
    )
    monkeypatch.setattr(
        server, "prepare_profile", lambda: calls["prepared"].append("profile")
    )
    monkeypatch.setattr(server, "load_model", lambda: calls["prepared"].append("model"))
    monkeypatch.setattr(
        webbrowser, "open", lambda address: calls["browser"].append(address)
    )
    monkeypatch.setattr(
        uvicorn, "run", lambda app, **options: calls["uvicorn"].append(options)
    )
    monkeypatch.setattr(
        server, "open_when_ready", lambda *args: calls["waiter"].append(args)
    )
    yield calls


def test_the_page_knowledge_base_profile_and_model_are_ready_before_requests(
    started: dict[str, list[object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "port_is_free", lambda host, port: True)

    assert server.serve(open_browser=False) == cli.EXIT_OK

    assert started["prepared"] == ["page", "knowledge base", "profile", "model"]
    assert len(started["uvicorn"]) == 1


def test_a_free_port_starts_the_service_and_opens_the_page_once_it_answers(
    started: dict[str, list[object]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(server, "port_is_free", lambda host, port: True)
    caplog.set_level("INFO", logger="chat_bridge")

    assert server.serve() == cli.EXIT_OK

    assert started["uvicorn"] == [
        {"host": "127.0.0.1", "port": 8000, "timeout_graceful_shutdown": 5}
    ]
    assert started["waiter"] == [("127.0.0.1", 8000, "http://127.0.0.1:8000")]
    assert "The chat page is at http://127.0.0.1:8000" in caplog.text


def test_without_the_browser_nothing_is_opened(
    started: dict[str, list[object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "port_is_free", lambda host, port: True)

    server.serve(open_browser=False)

    assert started["waiter"] == []
    assert started["browser"] == []


def test_a_port_held_by_chat_bridge_says_it_is_running_and_opens_that_page(
    started: dict[str, list[object]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(server, "port_is_free", lambda host, port: False)
    monkeypatch.setattr(server, "runs_chat_bridge", lambda address: True)
    caplog.set_level("INFO", logger="chat_bridge")

    assert server.serve() == cli.EXIT_OK

    assert "Already running. The chat page is at http://127.0.0.1:8000" in caplog.text
    assert started["browser"] == ["http://127.0.0.1:8000"]
    assert started["uvicorn"] == []
    # The running service keeps its page and its database to itself.
    assert started["prepared"] == []


def test_a_port_held_by_another_program_is_explained_in_words(
    started: dict[str, list[object]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(server, "port_is_free", lambda host, port: False)
    monkeypatch.setattr(server, "runs_chat_bridge", lambda address: False)

    assert server.serve() == cli.EXIT_ERROR

    assert (
        "port 8000 on 127.0.0.1 is used by another program" in capsys.readouterr().err
    )
    assert started["uvicorn"] == []
    assert started["browser"] == []


def test_the_port_check_sees_a_listening_socket() -> None:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        assert server.port_is_free("127.0.0.1", port) is False


def test_the_page_opens_only_once_the_port_accepts_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", lambda address: opened.append(address))
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        waiter = threading.Thread(
            target=server.open_when_ready, args=("127.0.0.1", port, "http://page")
        )
        waiter.start()
        waiter.join(timeout=0.6)
        assert opened == []

        listener.listen()
        waiter.join(timeout=5)

    assert opened == ["http://page"]


def test_the_command_passes_no_browser_on(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[bool] = []

    def serve(open_browser: bool = True) -> int:
        seen.append(open_browser)
        return cli.EXIT_OK

    monkeypatch.setattr(server, "serve", serve)

    cli.main(["--no-browser"])
    cli.main([])

    assert seen == [False, True]


# --- The knowledge base on the first run -------------------------------------------------


def _knowledge_base(
    monkeypatch: pytest.MonkeyPatch,
    *,
    empty: bool,
    refreshed: ingest_service.IngestReport | None = None,
) -> list[Path]:
    """Stands in for the knowledge base: what the refresh found, whether it is empty; returns
    the folders ingested."""
    ingested: list[Path] = []

    async def refresh() -> ingest_service.IngestReport:
        return refreshed or ingest_service.IngestReport()

    async def is_empty() -> bool:
        return empty

    async def ingest(root: Path) -> ingest_service.IngestReport:
        ingested.append(root)
        return ingest_service.IngestReport()

    monkeypatch.setattr(ingest_service, "refresh_index", refresh)
    monkeypatch.setattr(ingest_service, "knowledge_base_is_empty", is_empty)
    monkeypatch.setattr(ingest_service, "ingest_folder", ingest)
    return ingested


def test_an_empty_knowledge_base_is_filled_with_the_sample_news_first(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    ingested = _knowledge_base(monkeypatch, empty=True)
    caplog.set_level("INFO", logger="chat_bridge")

    server.prepare_knowledge_base()

    assert ingested == [server.SAMPLE_NEWS]
    assert (
        "The knowledge base is empty, so the sample news in data/truth" in caplog.text
    )
    assert "2.3 GB embedding model" in caplog.text


def test_a_knowledge_base_with_content_is_left_as_it_is(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    ingested = _knowledge_base(monkeypatch, empty=False)
    caplog.set_level("INFO", logger="chat_bridge")

    server.prepare_knowledge_base()

    assert ingested == []
    assert caplog.text == ""


def test_a_knowledge_base_an_earlier_version_made_is_cleared_and_the_sample_ingested(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    cleared = ingest_service.IngestReport(outdated=["documents.markets is missing"])
    ingested = _knowledge_base(monkeypatch, empty=True, refreshed=cleared)
    caplog.set_level("INFO", logger="chat_bridge")

    server.prepare_knowledge_base()

    assert ingested == [server.SAMPLE_NEWS]
    assert (
        "made by an earlier version of chat-bridge (documents.markets is missing), so it "
        "was cleared" in caplog.text
    )


def test_an_index_built_another_way_is_rebuilt_and_said(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    rebuilt = ingest_service.IngestReport(
        index_update=ingest_service.IndexUpdate.KEYWORDS
    )
    ingested = _knowledge_base(monkeypatch, empty=False, refreshed=rebuilt)
    caplog.set_level("INFO", logger="chat_bridge")

    server.prepare_knowledge_base()

    assert ingested == []
    assert "The search index was built another way, so it was rebuilt" in caplog.text


def test_other_tables_from_another_version_stop_the_service_with_why(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def refresh() -> ingest_service.IngestReport:
        return ingest_service.IngestReport()

    async def old() -> bool:
        raise SchemaMismatchError(["holdings.names is missing"])

    monkeypatch.setattr(server, "port_is_free", lambda host, port: True)
    monkeypatch.setattr(web, "prepare_page", lambda: tmp_path)
    monkeypatch.setattr(ingest_service, "refresh_index", refresh)
    monkeypatch.setattr(ingest_service, "knowledge_base_is_empty", old)

    assert server.serve() == cli.EXIT_ERROR

    error = capsys.readouterr().err
    assert "made by another version" in error
    assert "holdings.names is missing" in error
