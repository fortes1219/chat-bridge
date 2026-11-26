"""`chat-bridge collect` from the channels and from addresses, with a stand-in agent, stand-in pages
and fixed closes: one command from the events to truth files, and no ingest."""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest

from chat_bridge import cli
from chat_bridge.chat.programs import Login, LoginStatus, Program
from chat_bridge.chat.service import NoLoginError
from chat_bridge.collect import channels, pages, service
from chat_bridge.collect import cli as collect_cli
from chat_bridge.collect.channels import Channel
from chat_bridge.collect.pages import Read
from tests.collect import stand_ins
from tests.collect.stand_ins import CNA, FED, PAGES, checks_all, record
from tests.collect.test_moves import LISTED

CHANNELS = (
    Channel("fed", "Fed", "https://www.federalreserve.gov/newsevents/", (), ""),
    Channel("cna", "CNA", "https://www.cna.com.tw/list/afe.aspx", (), ""),
)
FOUND = {
    "events": [
        {
            "event_date": "2026-11-24",
            "about": "The Fed holds rates; the TAIEX rises",
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

    asked: list[str] = field(default_factory=list)

    def read_addresses(self, urls: Iterable[str]) -> Read:
        wanted = list(urls)
        self.asked += wanted
        return Read(tuple(page for page in PAGES if page.asked in wanted), ())


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


def _stand_ins(monkeypatch: pytest.MonkeyPatch, agent: _Agent, reader: _Reader) -> None:
    async def choose(requested: None) -> Program:
        return Program.CLAUDE_CODE

    monkeypatch.setattr(collect_cli, "choose_program", choose)
    monkeypatch.setattr(collect_cli, "PROGRAMS", {Program.CLAUDE_CODE: agent})
    monkeypatch.setattr(channels, "enabled_channels", lambda: CHANNELS)
    monkeypatch.setattr(pages, "Reader", lambda **kwargs: reader)
    monkeypatch.setattr(collect_cli, "market_series", lambda: LISTED)
    monkeypatch.setattr(
        service, "closes_for", lambda dates, now, listed: stand_ins.closes()
    )


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "truth"
    folder.mkdir()
    # The folder's latest event: the search starts from its date.
    (folder / "2026-11-18-fomc-minutes.md").write_text(
        "---\ntitle: 聯準會公布會議紀錄\nsources: []\n---\n", encoding="utf-8"
    )
    return folder


def test_one_command_makes_the_channels_events_into_files_and_ingests_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    agent = _Agent([record(), checks_all], found=FOUND)
    reader = _Reader()
    _stand_ins(monkeypatch, agent, reader)

    code = cli.main(["collect", "--into", str(folder), "--until", "2026-11-25"])

    assert code == cli.EXIT_OK
    assert (folder / "2026-11-24-fed-holds-taiex-rises.md").is_file()
    assert "from 2026-11-18 to 2026-11-25" in agent.searched[0]
    assert "2026-11-18  聯準會公布會議紀錄" in agent.searched[0]
    assert reader.asked == [FED.url, CNA.url]
    out = capsys.readouterr().out
    assert "Event 1 of 1: 2026-11-24  The Fed holds rates; the TAIEX rises" in out
    assert "    conversion  新台幣1兆2129.57億元 -> NT$1.212957 trillion" in out
    assert out.rstrip().endswith(
        f"Add them to the knowledge base: uv run chat-bridge ingest {folder}"
    )


def test_addresses_are_read_and_sorted_into_events(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
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
    agent = _Agent([groups, record(), checks_all])
    _stand_ins(monkeypatch, agent, _Reader())

    code = cli.main(["collect", FED.url, CNA.url, "--into", str(folder)])

    assert code == cli.EXIT_OK
    assert (folder / "2026-11-24-fed-holds-taiex-rises.md").is_file()
    assert agent.searched == []
    assert '<page id="p2"' in agent.asked[0][1]
    assert "Found 1 events." in capsys.readouterr().out


def test_a_page_that_moved_off_its_channels_site_is_not_used(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = _folder(tmp_path)
    moved = replace(CNA, url="https://elsewhere.example/news/1")

    @dataclass
    class _Moving(_Reader):
        def read_addresses(self, urls: Iterable[str]) -> Read:
            read = super().read_addresses(urls)
            return Read(
                tuple(moved if page is CNA else page for page in read.pages), ()
            )

    def fed_only(made: dict[str, Any]) -> None:
        for section in made["sections"]:
            section["items"] = [
                item for item in section["items"] if item["source"] == "s1"
            ]
            section["notes"] = [] if section["items"] else ["本檔讀過的來源沒有記載。"]
        made["sources"] = made["sources"][:1]
        made["conversions"] = []
        made["title"] = "聯準會利率維持不變"

    agent = _Agent([record(fed_only), checks_all], found=FOUND)
    _stand_ins(monkeypatch, agent, _Moving())

    code = cli.main(["collect", "--into", str(folder), "--until", "2026-11-25"])

    out = capsys.readouterr().out
    assert code == cli.EXIT_NOT_ALL
    assert (
        f"    not used  {CNA.url}: it moved to https://elsewhere.example/news/1" in out
    )
    # The writing run got the Fed page only.
    assert 'id="s2"' not in agent.asked[0][1]


def test_no_file_written_gives_no_ingest_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_date(made: dict[str, Any]) -> None:
        made["event_date"] = "someday"

    agent = _Agent([record(no_date), record(no_date)], found=FOUND)
    _stand_ins(monkeypatch, agent, _Reader())

    code = cli.main(
        ["collect", "--into", str(_folder(tmp_path)), "--until", "2026-11-25"]
    )

    out = capsys.readouterr().out
    assert code == cli.EXIT_NOT_ALL
    assert "Files: 0 written" in out and "uv run chat-bridge ingest" not in out


def test_a_search_past_its_limit_says_to_ask_for_fewer_days(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _stand_ins(monkeypatch, _Agent([]), _Reader())
    monkeypatch.setattr(channels, "TIME_LIMIT_SECONDS", 0.01)

    code = cli.main(["collect", "--into", str(_folder(tmp_path))])

    assert code == cli.EXIT_ERROR
    assert "--until" in capsys.readouterr().err


def test_with_no_program_logged_in_nothing_is_asked_or_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    agent = _Agent([], found=FOUND)
    reader = _Reader()
    _stand_ins(monkeypatch, agent, reader)

    async def no_login(requested: None) -> Program:
        raise NoLoginError(LoginStatus(Login.NOT_LOGGED_IN, "none"))

    monkeypatch.setattr(collect_cli, "choose_program", no_login)

    assert cli.main(["collect", "--into", str(_folder(tmp_path))]) == cli.EXIT_ERROR
    assert agent.searched == [] and reader.asked == []
    assert "claude auth login" in capsys.readouterr().err


def test_news_files_get_their_market_moves_and_are_not_ingested(
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
