"""Collecting from the channels: the list, the agent's question and answer, how each program is
started, and one command from the channels to the knowledge base. No program is started."""

import asyncio
import json
from datetime import date
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from chat_bridge import cli
from chat_bridge.chat import claude_code, codex
from chat_bridge.chat.programs import Login, LoginStatus, Program, ProgramError
from chat_bridge.chat.service import NoLoginError
from chat_bridge.collect import channels, pages
from chat_bridge.collect import cli as collect_cli
from chat_bridge.collect.channels import (
    FOUND_SCHEMA,
    Channel,
    ChannelsFileError,
    SearchError,
    enabled_channels,
    question,
    read_found,
    search_channels,
)

CNA = Channel("cna", "CNA", "https://www.cna.com.tw/list/afe.aspx", ("taiwan",), "")
FED = Channel(
    "fed", "Fed", "https://www.federalreserve.gov/newsevents/pressreleases.htm", (), ""
)
LISTED = (CNA, FED)


def _write_channels(tmp_path: Path, entries: list[dict[str, Any]]) -> Path:
    path = tmp_path / "channels.json"
    path.write_text(json.dumps({"about": "x", "channels": entries}), encoding="utf-8")
    return path


def _entry(**changes: Any) -> dict[str, Any]:
    base = {
        "id": "a",
        "name": "A",
        "url": "https://a.example.com/",
        "enabled": True,
        "topics": [],
        "note": "",
    }
    return {**base, **changes}


def test_the_sample_list_is_read_and_only_enabled_channels_are_used(
    tmp_path: Path,
) -> None:
    assert len(enabled_channels()) == 13
    path = _write_channels(tmp_path, [_entry(), _entry(id="b", enabled=False)])

    assert [one.id for one in enabled_channels.__wrapped__(path)] == ["a"]


@pytest.mark.parametrize(
    ("entries", "reason"),
    [
        ([_entry(), _entry()], "listed twice"),
        ([_entry(url="ftp://a.example.com/")], "not a web address"),
        ([_entry(kind="rss")], "Extra inputs"),
    ],
)
def test_a_list_not_in_its_shape_is_refused(
    tmp_path: Path, entries: list[dict[str, Any]], reason: str
) -> None:
    with pytest.raises(ChannelsFileError, match=reason):
        enabled_channels.__wrapped__(_write_channels(tmp_path, entries))


def test_the_question_gives_the_date_and_the_channels_as_data() -> None:
    text = question(LISTED, date(2026, 11, 25))

    assert text.startswith("Find the articles published on or after 2026-11-25.")
    assert '"id": "cna"' in text and "<channels>" in text
    assert question(LISTED, None).startswith("Find the latest articles.")


def test_each_page_must_be_on_its_channels_site_and_each_channel_is_counted() -> None:
    cna_page = "https://www.cna.com.tw/news/afe/202611250001.aspx"
    reply = {
        "pages": [
            {"url": cna_page, "channel": "cna"},
            {"url": cna_page, "channel": "cna"},
            {"url": "https://m.www.federalreserve.gov/a.htm", "channel": "fed"},
            {"url": "https://made-up.example.org/fed", "channel": "fed"},
            {"url": "https://www.cna.com.tw/news/2.aspx", "channel": "fed"},
            {"url": "https://www.cna.com.tw/news/3.aspx", "channel": "bbc"},
        ]
    }

    found = read_found(reply, LISTED)

    assert found.pages == (cna_page, "https://m.www.federalreserve.gov/a.htm")
    assert found.per_channel == {"cna": 1, "fed": 1}
    assert found.refused == (
        ("https://made-up.example.org/fed", "it is not on the site of channel fed"),
        ("https://www.cna.com.tw/news/2.aspx", "it is not on the site of channel fed"),
        ("https://www.cna.com.tw/news/3.aspx", "it names no listed channel (bbc)"),
    )


class _Program:
    """A stand-in program: its web search answers with the given function."""

    def __init__(self, finder: Any) -> None:
        self.web_reply_in_shape = finder


def _search(
    finder: Any,
    since: date | None = date(2026, 11, 25),
    listed: tuple[Channel, ...] = LISTED,
) -> channels.Search:
    async def choose(requested: None) -> Program:
        return Program.CLAUDE_CODE

    async def latest() -> date | None:
        return since

    return asyncio.run(
        search_channels(
            listed,
            lambda line: None,
            programs={Program.CLAUDE_CODE: _Program(finder)},  # type: ignore[dict-item]
            choose=choose,
            latest=latest,
        )
    )


def test_with_no_channel_enabled_the_agent_is_not_asked() -> None:
    asked: list[object] = []

    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        asked.append(args)
        return {"pages": []}

    with pytest.raises(SearchError, match="no channel is enabled"):
        _search(finder, listed=())
    assert asked == []


def test_the_agent_is_asked_once_with_the_channels_sites_and_the_schema() -> None:
    asked: list[tuple[Any, ...]] = []

    async def finder(
        prompt: str,
        text: str,
        schema: dict[str, Any],
        sites: list[str],
        *,
        on_start: Any,
    ) -> dict[str, Any]:
        asked.append((text, schema, sites))
        return {
            "pages": [{"url": "https://www.cna.com.tw/news/1.aspx", "channel": "cna"}]
        }

    search = _search(finder)

    assert len(asked) == 1
    text, schema, sites = asked[0]
    assert schema is FOUND_SCHEMA and sites == [
        "www.cna.com.tw",
        "www.federalreserve.gov",
    ]
    assert "on or after 2026-11-25" in text
    assert search.found.pages == ("https://www.cna.com.tw/news/1.aspx",)


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        (ProgramError("Claude Code exited with code 1"), "exited with code 1"),
        ({"pages": "none"}, "not in the asked-for shape"),
    ],
)
def test_a_failed_run_or_an_answer_in_another_shape_collects_nothing(
    answer: Any, message: str
) -> None:
    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if isinstance(answer, Exception):
            raise answer
        result: dict[str, Any] = answer
        return result

    with pytest.raises(SearchError, match=message):
        _search(finder)


def test_a_run_past_its_limit_collects_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(channels, "TIME_LIMIT_SECONDS", 0.01)

    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(1)
        return {"pages": []}

    with pytest.raises(SearchError, match="did not finish"):
        _search(finder)


def test_the_chats_own_claude_code_start_is_unchanged() -> None:
    args = claude_code.shaped_command_line(
        "claude", {"type": "object"}, "p.md", claude_code.NO_TOOLS
    )

    assert args == [
        "claude",
        "-p",
        "--restricted",
        "--strict-mcp-config",
        "--tools",
        "",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        '{"type":"object"}',
        "--system-prompt-file",
        "p.md",
    ]


def test_claude_code_searching_gets_web_search_and_reading_on_the_sites_only() -> None:
    args = claude_code.shaped_command_line(
        "claude", {}, "p.md", claude_code.web_tool_args(["www.cna.com.tw"])
    )

    tools = args[args.index("--tools") + 1]
    allowed = args[args.index("--allowedTools") + 1].split(",")
    assert tools == "WebSearch,WebFetch"
    assert allowed == [
        "WebSearch",
        "WebFetch(domain:www.cna.com.tw)",
        "WebFetch(domain:*.www.cna.com.tw)",
    ]
    assert "--restricted" in args and "--strict-mcp-config" in args


def test_codex_searching_turns_on_live_search_and_keeps_the_rest_off() -> None:
    chat = codex.shaped_command_line("codex", "folder", "schema.json")
    search = codex.shaped_command_line(
        "codex", "folder", "schema.json", codex.WEB_GLOBAL_ARGS
    )

    assert "web_search='disabled'" in chat and "web_search='live'" not in chat
    assert "web_search='live'" in search and "web_search='disabled'" not in search
    assert [arg for arg in search if arg != "web_search='live'"] == [
        arg for arg in chat if arg != "web_search='disabled'"
    ]
    assert search[search.index("--sandbox") + 1] == "read-only"


PAGE = "https://www.cna.com.tw/news/1.aspx"


def _stand_ins(
    monkeypatch: pytest.MonkeyPatch, kind: pages.Kind, ingested: list[Path]
) -> None:
    async def search(listed: Any, progress: Any) -> channels.Search:
        found = channels.Found((PAGE,), {"cna": 1, "fed": 0}, ())
        return channels.Search(Program.CODEX, None, found)

    def collect(urls: list[str], folder: Path, *, progress: Any) -> list[pages.Outcome]:
        return [pages.Outcome(url, kind, "t", folder / "a.md") for url in urls]

    async def ingest(root: Path, *, replace: bool = False) -> Any:
        ingested.append(root)
        return type("Report", (), {"written": [], "unchanged": [], "rejected": []})()

    monkeypatch.setattr(channels, "search_channels", search)
    monkeypatch.setattr(pages, "collect_addresses", collect)
    monkeypatch.setattr(collect_cli.ingest_service, "ingest_folder", ingest)


def test_one_command_collects_the_channels_pages_and_ingests_them(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ingested: list[Path] = []
    _stand_ins(monkeypatch, "written", ingested)

    assert cli.main(["collect", "--into", str(tmp_path)]) == cli.EXIT_OK

    assert ingested == [tmp_path.resolve()]
    out = capsys.readouterr().out
    assert "    1  cna\n" in out and "    0  fed\n" in out
    assert "uv run chat-bridge ingest" not in out
    assert f"Adding {tmp_path} to the knowledge base." in out


def test_pages_collected_unchanged_are_still_ingested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A run that stopped before its ingest left the pages; the next run adds them.
    ingested: list[Path] = []
    _stand_ins(monkeypatch, "unchanged", ingested)

    assert cli.main(["collect", "--into", str(tmp_path)]) == cli.EXIT_OK
    assert ingested == [tmp_path.resolve()]


def test_with_no_program_logged_in_nothing_is_asked_or_collected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    collected: list[object] = []

    async def no_login(requested: None) -> Program:
        raise NoLoginError(LoginStatus(Login.NOT_LOGGED_IN, "none"))

    monkeypatch.setattr(
        channels, "search_channels", partial(channels.search_channels, choose=no_login)
    )
    monkeypatch.setattr(
        pages, "collect_addresses", lambda *args, **kwargs: collected.append(args)
    )

    assert cli.main(["collect", "--into", str(tmp_path)]) == cli.EXIT_ERROR
    assert collected == []
    assert "claude auth login" in capsys.readouterr().err


def test_news_files_are_not_ingested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    news = tmp_path / "news.md"
    news.write_text("x", encoding="utf-8")
    ingested: list[Path] = []

    async def ingest(root: Path, *, replace: bool = False) -> Any:
        ingested.append(root)

    monkeypatch.setattr(collect_cli.ingest_service, "ingest_folder", ingest)
    monkeypatch.setattr(collect_cli.service, "collect_market_moves", lambda files: [])

    assert cli.main(["collect", str(news)]) == cli.EXIT_OK
    assert ingested == []
