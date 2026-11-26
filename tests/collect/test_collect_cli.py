"""`chat-bridge collect` from the channels and from addresses, with a stand-in agent and stand-in
pages: the events found are read once and stored for `truth`; no truth file is written and no
model writes a record."""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest

from chat_bridge import cli
from chat_bridge.chat.programs import Login, LoginStatus, Program
from chat_bridge.chat.service import NoLoginError
from chat_bridge.collect import channels, pages, service, store
from chat_bridge.collect import cli as collect_cli
from chat_bridge.collect.channels import Channel
from chat_bridge.collect.pages import Read
from tests.truth import stand_ins
from tests.truth.stand_ins import CNA, FED, FOUND_DATE, PAGES

CHANNELS = (
    Channel("fed", "Fed", "https://www.federalreserve.gov/newsevents/", (), ""),
    Channel("cna", "CNA", "https://www.cna.com.tw/list/afe.aspx", (), ""),
)
ABOUT = "The Fed holds rates; the TAIEX rises"
FOUND = {
    "events": [
        {
            "event_date": "2026-11-24",
            "about": ABOUT,
            "pages": [
                {"url": FED.url, "channel": "fed"},
                {"url": CNA.url, "channel": "cna"},
            ],
        }
    ]
}


@dataclass
class _Reader:
    """Stand-in pages: each address asked gives its saved page."""

    pages: tuple[Any, ...] = PAGES
    asked: list[str] = field(default_factory=list)

    def read_addresses(self, urls: Iterable[str]) -> Read:
        wanted = list(urls)
        self.asked += wanted
        return Read(tuple(page for page in self.pages if page.asked in wanted), ())


@dataclass
class _Agent(stand_ins.Program):
    found: Any = None
    searched: list[str] = field(default_factory=list)

    async def web_reply_in_shape(
        self, prompt: str, text: str, schema: Any, sites: Any, *, on_start: Any
    ) -> dict[str, Any]:
        self.searched.append(text)
        if self.found is None:
            # A search that does not finish.
            await asyncio.sleep(1)
        result: dict[str, Any] = self.found
        return result


@dataclass
class _Places:
    truth: Path
    collected: Path


def _stand_ins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, agent: _Agent, reader: _Reader
) -> _Places:
    async def choose(requested: None) -> Program:
        return Program.CLAUDE_CODE

    truth = tmp_path / "truth"
    truth.mkdir()
    # The truth folder's latest event: the search starts from its date.
    (truth / "2026-11-18-fomc-minutes.md").write_text(
        "---\ntitle: 聯準會公布會議紀錄\nsources: []\n---\n", encoding="utf-8"
    )
    collected = tmp_path / "collected"
    monkeypatch.setattr(collect_cli, "choose_program", choose)
    monkeypatch.setattr(collect_cli, "PROGRAMS", {Program.CLAUDE_CODE: agent})
    monkeypatch.setattr(collect_cli, "TRUTH_FOLDER", truth)
    monkeypatch.setattr(channels, "enabled_channels", lambda: CHANNELS)
    monkeypatch.setattr(pages, "Reader", lambda **kwargs: reader)
    monkeypatch.setattr(store, "collected_dir", lambda: collected)
    return _Places(truth, collected)


def test_the_channels_events_are_read_once_and_stored_and_no_file_is_written(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = _Agent([], found=FOUND)
    reader = _Reader()
    places = _stand_ins(monkeypatch, tmp_path, agent, reader)

    code = cli.main(["collect", "--until", "2026-11-25"])

    assert code == cli.EXIT_OK
    (event,) = store.stored_events(places.collected)
    assert (event.event_date, event.about) == (FOUND_DATE, ABOUT)
    assert event.read_pages() == PAGES
    assert [path.name for path in places.truth.iterdir()] == [
        "2026-11-18-fomc-minutes.md"
    ]
    # One search; no model run writes anything.
    assert len(agent.searched) == 1 and agent.asked == []
    assert "from 2026-11-18 to 2026-11-25" in agent.searched[0]
    assert "2026-11-18  聯準會公布會議紀錄" in agent.searched[0]
    assert reader.asked == [FED.url, CNA.url]
    out = capsys.readouterr().out
    assert f"Event 1 of 1: 2026-11-24  {ABOUT}" in out
    assert out.rstrip().endswith("Make them into truth files: uv run chat-bridge truth")


def test_an_event_stored_already_is_not_read_again_and_the_search_is_told(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = _Agent([], found=FOUND)
    reader = _Reader()
    places = _stand_ins(monkeypatch, tmp_path, agent, reader)
    cli.main(["collect", "--until", "2026-11-25"])
    reader.asked.clear()

    cli.main(["collect", "--until", "2026-11-25"])

    assert reader.asked == []
    assert f"2026-11-24  {ABOUT}" in agent.searched[1]
    assert len(store.stored_events(places.collected)) == 1
    assert f"  already stored  {ABOUT}" in capsys.readouterr().out


def test_a_page_that_moved_off_its_channels_site_is_not_stored(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    moved = replace(CNA, url="https://elsewhere.example/news/1")
    places = _stand_ins(
        monkeypatch, tmp_path, _Agent([], found=FOUND), _Reader(pages=(FED, moved))
    )

    code = cli.main(["collect", "--until", "2026-11-25"])

    assert code == cli.EXIT_NOT_ALL
    (event,) = store.stored_events(places.collected)
    assert event.read_pages() == (FED,)
    assert (
        f"    not used  {CNA.url}: it moved to https://elsewhere.example/news/1"
        in capsys.readouterr().out
    )


def test_addresses_are_read_sorted_into_events_and_stored(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    groups = {
        "events": [
            {
                "event_date": "2026-11-24",
                "about": "Fed and TAIEX",
                "pages": ["p1", "p2"],
            }
        ],
        "not_events": [],
    }
    agent = _Agent([groups])
    places = _stand_ins(monkeypatch, tmp_path, agent, _Reader())

    code = cli.main(["collect", FED.url, CNA.url])

    assert code == cli.EXIT_OK
    (event,) = store.stored_events(places.collected)
    assert event.about == "Fed and TAIEX" and event.read_pages() == PAGES
    assert agent.searched == [] and len(agent.asked) == 1
    assert '<page id="p2"' in agent.asked[0][1]
    assert "Stored 1 events in" in capsys.readouterr().out


def test_a_search_past_its_limit_says_to_ask_for_fewer_days(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    places = _stand_ins(monkeypatch, tmp_path, _Agent([]), _Reader())
    monkeypatch.setattr(channels, "TIME_LIMIT_SECONDS", 0.01)

    code = cli.main(["collect"])

    assert code == cli.EXIT_ERROR
    assert "--until" in capsys.readouterr().err
    assert not places.collected.exists()


def test_with_no_program_logged_in_nothing_is_asked_or_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = _Agent([], found=FOUND)
    reader = _Reader()
    _stand_ins(monkeypatch, tmp_path, agent, reader)

    async def no_login(requested: None) -> Program:
        raise NoLoginError(LoginStatus(Login.NOT_LOGGED_IN, "none"))

    monkeypatch.setattr(collect_cli, "choose_program", no_login)

    assert cli.main(["collect"]) == cli.EXIT_ERROR
    assert agent.searched == [] and reader.asked == []
    assert "claude auth login" in capsys.readouterr().err


def test_news_files_get_their_market_moves_as_before(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    news = tmp_path / "news.md"
    news.write_text("x", encoding="utf-8")
    asked: list[object] = []
    monkeypatch.setattr(
        service, "collect_market_moves", lambda files: asked.append(files) or []
    )

    assert cli.main(["collect", str(news)]) == cli.EXIT_OK
    assert asked == [[news]]
