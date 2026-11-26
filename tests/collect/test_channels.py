"""Finding events on the channels: the list, the agent's question and answer, and how each program
is started. No program is started."""

import asyncio
import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from chat_bridge.chat import claude_code, codex
from chat_bridge.chat.programs import ProgramError
from chat_bridge.collect import channels
from chat_bridge.collect.channels import (
    EVENTS_SCHEMA,
    Channel,
    ChannelsFileError,
    SearchError,
    enabled_channels,
    question,
    read_events,
    search_events,
)
from chat_bridge.collect.store import StoredEvent
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import read_rules
from chat_bridge.truth.truth_files import FolderEvent
from tests.truth.stand_ins import CNA as CNA_PAGE

CNA = Channel("cna", "CNA", "https://www.cna.com.tw/list/afe.aspx", ("taiwan",), "")
FED = Channel(
    "fed", "Fed", "https://www.federalreserve.gov/newsevents/pressreleases.htm", (), ""
)
LISTED = (CNA, FED)
WINDOW = Window(date(2026, 11, 18), date(2026, 11, 25))
HAVE = channels.held_events(
    [
        FolderEvent(
            Path("2026-11-19-fomc-minutes.md"),
            date(2026, 11, 19),
            "聯準會公布會議紀錄",
            frozenset(),
        )
    ],
    [
        StoredEvent(
            Path("2026-11-18-0123456789ab"),
            date(2026, 11, 18),
            "Stored, not yet a file",
            date(2026, 11, 17),
            None,
        )
    ],
)


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


def test_the_question_gives_the_dates_targets_events_held_and_channels() -> None:
    text = question(LISTED, read_rules(), WINDOW, HAVE)

    assert text.startswith("Find the events from 2026-11-18 to 2026-11-25.")
    assert "1. 2026 年 6 月起的台股與美股相關消息。" in text
    # The truth folder's events and the stored ones, by date.
    assert "2026-11-18  Stored, not yet a file\n2026-11-19  聯準會公布會議紀錄" in text
    assert '"id": "cna"' in text and "<channels>" in text
    assert question(LISTED, read_rules(), Window(None, None), []).startswith(
        "Find the latest events."
    )


def _page(url: str, channel: str) -> dict[str, str]:
    return {"url": url, "channel": channel}


def test_each_events_pages_must_be_on_their_channels_site() -> None:
    cna_page = "https://www.cna.com.tw/news/afe/202611250001.aspx"
    reply = {
        "events": [
            {
                "event_date": "2026-11-24",
                "about": "TAIEX rises",
                "pages": [
                    _page(cna_page, "cna"),
                    _page(cna_page, "cna"),
                    _page("https://m.www.federalreserve.gov/a.htm", "fed"),
                    _page("https://made-up.example.org/fed", "fed"),
                    _page("https://www.cna.com.tw/news/3.aspx", "bbc"),
                ],
            },
            {
                "event_date": "2026-11-20",
                "about": "only off-site pages",
                "pages": [_page("https://www.cna.com.tw/news/2.aspx", "fed")],
            },
        ]
    }

    found = read_events(reply, LISTED, WINDOW)

    assert [(one.about, one.pages) for one in found.events] == [
        ("TAIEX rises", (cna_page, "https://m.www.federalreserve.gov/a.htm"))
    ]
    assert found.refused == (
        ("https://made-up.example.org/fed", "it is not on the site of channel fed"),
        ("https://www.cna.com.tw/news/3.aspx", "it names no listed channel (bbc)"),
        ("https://www.cna.com.tw/news/2.aspx", "it is not on the site of channel fed"),
        ("only off-site pages", "none of its pages is on a channel's site"),
    )


def test_a_page_that_moved_off_its_channels_site_is_not_used() -> None:
    asked = "https://www.cna.com.tw/news/afe/1.aspx"
    reply = {
        "events": [
            {
                "event_date": "2026-11-24",
                "about": "TAIEX rises",
                "pages": [_page(asked, "cna")],
            }
        ]
    }
    event = read_events(reply, LISTED, WINDOW).events[0]
    same_site = replace(CNA_PAGE, asked=asked, url="https://www.cna.com.tw/news/2.aspx")
    moved = replace(CNA_PAGE, asked=asked, url="https://elsewhere.example/news/1")

    assert event.on_their_sites([same_site]) == ((same_site,), ())
    kept, refused = event.on_their_sites([moved])
    assert kept == ()
    assert refused == (
        (
            asked,
            "it moved to https://elsewhere.example/news/1, off its channel's site "
            "www.cna.com.tw",
        ),
    )


@pytest.mark.parametrize(
    ("event_date", "reason"),
    [
        ("2026-11-17", "its date 2026-11-17 is outside the asked dates"),
        ("2026-11-26", "its date 2026-11-26 is outside the asked dates"),
        ("Nov 24", "its date is not YYYY-MM-DD: Nov 24"),
    ],
)
def test_an_event_outside_the_asked_dates_is_not_used(
    event_date: str, reason: str
) -> None:
    reply = {
        "events": [
            {
                "event_date": event_date,
                "about": "x",
                "pages": [_page("https://www.cna.com.tw/n/1.aspx", "cna")],
            }
        ]
    }

    found = read_events(reply, LISTED, WINDOW)

    assert found.events == () and found.refused == (("x", reason),)


class _Program:
    """A stand-in program: its web search answers with the given function."""

    def __init__(self, finder: Any) -> None:
        self.web_reply_in_shape = finder


def _search(finder: Any, listed: tuple[Channel, ...] = LISTED) -> channels.Found:
    return asyncio.run(
        search_events(
            listed,
            read_rules(),
            WINDOW,
            HAVE,
            _Program(finder),  # type: ignore[arg-type]
            "Claude Code",
            lambda line: None,
        )
    )


def test_with_no_channel_enabled_the_agent_is_not_asked() -> None:
    asked: list[object] = []

    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        asked.append(args)
        return {"events": []}

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
            "events": [
                {
                    "event_date": "2026-11-24",
                    "about": "TAIEX rises",
                    "pages": [_page("https://www.cna.com.tw/news/1.aspx", "cna")],
                }
            ]
        }

    found = _search(finder)

    assert len(asked) == 1
    text, schema, sites = asked[0]
    assert schema is EVENTS_SCHEMA
    assert sites == ["www.cna.com.tw", "www.federalreserve.gov"]
    assert "from 2026-11-18 to 2026-11-25" in text
    assert found.events[0].pages == ("https://www.cna.com.tw/news/1.aspx",)


@pytest.mark.parametrize(
    ("answer", "message"),
    [
        (ProgramError("Claude Code exited with code 1"), "exited with code 1"),
        ({"events": "none"}, "not in the asked-for shape"),
    ],
)
def test_a_failed_run_or_an_answer_in_another_shape_finds_nothing(
    answer: Any, message: str
) -> None:
    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if isinstance(answer, Exception):
            raise answer
        result: dict[str, Any] = answer
        return result

    with pytest.raises(SearchError, match=message):
        _search(finder)


def test_a_run_past_its_limit_says_what_to_do_next(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(channels, "TIME_LIMIT_SECONDS", 0.01)

    async def finder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(1)
        return {"events": []}

    with pytest.raises(SearchError, match="did not finish") as raised:
        _search(finder)
    assert "--until" in str(raised.value) and "channels.json" in str(raised.value)


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
