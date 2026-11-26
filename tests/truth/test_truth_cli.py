"""`chat-bridge truth` over events `collect` stored, with a stand-in agent and fixed closes: each
stored event made into a file from its stored pages only, what was collected removed once it is a
file, the runs at once bounded, and a stop that leaves nothing half made."""

import asyncio
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from chat_bridge import cli
from chat_bridge.chat.programs import Program as ProgramId
from chat_bridge.collect import service, store
from chat_bridge.truth import cli as truth_cli
from tests.collect.test_moves import LISTED
from tests.truth import stand_ins
from tests.truth.stand_ins import CNA, FED, FOUND_DATE, PAGES, Program, record

SINCE = stand_ins.WINDOW.since
UNTIL = stand_ins.WINDOW.until
OTHER = "https://www.federalreserve.gov/newsevents/b.htm"


@dataclass
class _Places:
    truth: Path
    collected: Path


def _stand_ins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, program: Any
) -> _Places:
    async def choose(requested: None) -> ProgramId:
        return ProgramId.CLAUDE_CODE

    places = _Places(tmp_path / "truth", tmp_path / "collected")
    places.truth.mkdir()
    monkeypatch.setattr(truth_cli, "choose_program", choose)
    monkeypatch.setattr(truth_cli, "PROGRAMS", {ProgramId.CLAUDE_CODE: program})
    monkeypatch.setattr(truth_cli, "market_series", lambda: LISTED)
    monkeypatch.setattr(store, "collected_dir", lambda: places.collected)
    monkeypatch.setattr(
        service, "closes_for", lambda dates, now, listed: stand_ins.closes()
    )
    return places


def _store(
    places: _Places,
    about: str = "The Fed",
    pages: Any = PAGES,
    found: date = FOUND_DATE,
) -> None:
    store.store(places.collected, found, about, SINCE, UNTIL, pages)


def _truth(places: _Places, *options: str) -> int:
    return cli.main(["truth", "--into", str(places.truth), *options])


def test_a_stored_event_becomes_a_file_and_what_was_collected_is_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    program = Program([record()])
    places = _stand_ins(monkeypatch, tmp_path, program)
    _store(places)

    code = _truth(places)

    assert code == cli.EXIT_OK
    written = places.truth / "2026-11-24-fed-holds-taiex-rises.md"
    assert written.is_file()
    # The stored pages' text is what the agent was given; one run for the event.
    assert len(program.asked) == 1 and CNA.text in program.asked[0][1]
    assert not places.collected.exists()
    out = capsys.readouterr().out
    assert f"Event 1 of 1: written        {written}" in out
    assert "    conversion  新台幣1兆2129.57億元 -> NT$1.212957 trillion" not in out
    assert "  [1/1] conversion  新台幣1兆2129.57億元 -> NT$1.212957 trillion" in out
    assert out.rstrip().endswith(
        f"Add them to the knowledge base: uv run chat-bridge ingest {places.truth}"
    )


def test_an_event_the_folder_has_is_removed_without_a_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    program = Program([])
    places = _stand_ins(monkeypatch, tmp_path, program)
    (places.truth / "2026-11-24-fed.md").write_text(
        f"---\ntitle: x\nsources:\n  - id: s1\n    url: {FED.url}\n  - id: s2\n"
        f"    url: {CNA.url}\n---\n",
        encoding="utf-8",
    )
    _store(places)

    assert _truth(places) == cli.EXIT_OK
    assert program.asked == [] and not places.collected.exists()


def test_an_event_not_written_twice_is_kept_listed_and_tried_next_time(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def bad(made: dict[str, Any]) -> None:
        made["exposure"] = ["crypto"]

    places = _stand_ins(monkeypatch, tmp_path, Program([record(bad), record(bad)]))
    _store(places)

    code = _truth(places)

    assert code == cli.EXIT_NOT_ALL
    (kept,) = store.stored_events(places.collected)
    out = capsys.readouterr().out
    assert "uses your subscription again" in out
    assert f"  [1] 2026-11-24  The Fed  ({kept.folder.name})" in out
    assert "uv run chat-bridge ingest" not in out
    assert list(places.truth.iterdir()) == []


def test_limit_makes_only_the_first_stored_events(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    program = _Waiting()
    places = _stand_ins(monkeypatch, tmp_path, program)
    _three_fed_events(places)
    first = store.stored_events(places.collected)[0]

    assert _truth(places, "--limit", "1") == cli.EXIT_OK
    assert len(program.started) == 1
    assert first.about in program.started[0]
    assert len(store.stored_events(places.collected)) == 2


@dataclass
class _Waiting:
    """A stand-in program whose runs wait, counting how many are under way at once; each run
    answers with the record, its slug the same for all."""

    release: asyncio.Event | None = None
    running: int = 0
    most: int = 0
    stopped: int = 0
    started: list[str] = field(default_factory=list)

    async def reply_in_shape(
        self, prompt: str, text: str, schema: Any, *, on_start: Any
    ) -> dict[str, Any]:
        self.running += 1
        self.most = max(self.most, self.running)
        self.started.append(text)
        try:
            if self.release is not None:
                await self.release.wait()
            else:
                await asyncio.sleep(0.05)
            ids = schema["properties"]["sources"]["items"]["properties"]["id"]["enum"]
            return _answer_for(ids)
        finally:
            self.running -= 1
            self.stopped += 1


def _answer_for(ids: list[str]) -> dict[str, Any]:
    """The Fed-only record, for an event whose one source is the Fed page."""

    def fed_only(made: dict[str, Any]) -> None:
        for section in made["sections"]:
            section["items"] = [
                item for item in section["items"] if item["source"] == "s1"
            ]
            section["notes"] = [] if section["items"] else ["本檔讀過的來源沒有記載。"]
        made["sources"] = made["sources"][:1]
        made["conversions"] = []
        made["title"] = "聯準會利率維持不變"

    return record(fed_only) if ids == ["s1"] else record()


def _fed_event(places: _Places, number: int, found: date) -> None:
    url = f"https://www.federalreserve.gov/newsevents/{number}.htm"
    _store(places, f"event {number}", (replace(FED, asked=url, url=url),), found)


def _three_fed_events(places: _Places) -> None:
    """Three events found for three dates, so they may run at once."""
    for number in range(3):
        _fed_event(places, number, date(2026, 11, 22 + number))


def test_events_of_one_date_run_one_after_another_and_see_each_others_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    program = _Waiting()
    places = _stand_ins(monkeypatch, tmp_path, program)
    _fed_event(places, 0, FOUND_DATE)
    _fed_event(places, 1, FOUND_DATE)

    assert _truth(places) == cli.EXIT_OK

    assert program.most == 1
    first, second = program.started
    assert "2026-11-24-fed-holds-taiex-rises.md" not in first
    assert "2026-11-24-fed-holds-taiex-rises.md  聯準會利率維持不變" in second


def test_at_most_workers_runs_are_under_way_and_names_never_clash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    program = _Waiting()
    places = _stand_ins(monkeypatch, tmp_path, program)
    _three_fed_events(places)

    assert _truth(places, "--workers", "2") == cli.EXIT_OK

    assert program.most == 2
    names = sorted(path.name for path in places.truth.iterdir())
    assert names == [
        "2026-11-24-fed-holds-taiex-rises-2.md",
        "2026-11-24-fed-holds-taiex-rises-3.md",
        "2026-11-24-fed-holds-taiex-rises.md",
    ]
    assert not places.collected.exists()


def test_a_stop_ends_every_run_under_way_and_leaves_nothing_half_made(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    program = _Waiting()
    places = _stand_ins(monkeypatch, tmp_path, program)
    _three_fed_events(places)

    async def stop_while_two_run() -> None:
        program.release = asyncio.Event()
        task = asyncio.create_task(truth_cli._make(places.truth, None, 2))
        while program.running < 2:
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(stop_while_two_run())

    assert program.running == 0 and program.stopped == 2
    assert list(places.truth.iterdir()) == []
    assert len(store.stored_events(places.collected)) == 3

    # The next run makes them all, reading nothing again.
    program.release = None
    assert _truth(places) == cli.EXIT_OK
    assert len(list(places.truth.iterdir())) == 3
    assert not places.collected.exists()


def test_with_nothing_stored_it_says_to_collect_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    places = _stand_ins(monkeypatch, tmp_path, Program([]))

    assert _truth(places) == cli.EXIT_OK
    assert "Collect first: uv run chat-bridge collect" in capsys.readouterr().out
