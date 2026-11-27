"""An event made into a truth file with a stand-in agent, stored pages and fixed closes (spec
SC-001, SC-002): the file section by section, each refusal, the second asking, a run stopped part
way."""

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from chat_bridge.chat.programs import ProgramError
from chat_bridge.truth.maker import EventOutcome
from chat_bridge.truth.truth_files import PART_SUFFIX, folder_events
from tests.truth.stand_ins import (
    CNA,
    FED,
    Program,
    make,
    maker,
    record,
)


def _make(
    folder: Path,
    program: Program,
    conversions: Path | None = None,
    told: list[str] | None = None,
) -> EventOutcome:
    built = maker(folder, program, conversions=conversions)
    return asyncio.run(make(built, told=told))


def _sections(text: str) -> list[str]:
    return [line for line in text.split("\n") if line.startswith("## ")]


def test_a_two_source_event_becomes_one_file_in_the_format(tmp_path: Path) -> None:
    conversions = tmp_path / "number_conversions.md"
    conversions.write_text(
        "| 檔名 | 來源原寫法 | 轉成 | 註 |\n|---|---|---|---|\n", encoding="utf-8"
    )
    folder = tmp_path / "truth"

    program = Program([record()])

    outcome = _make(folder, program, conversions=conversions)

    # One run of the program for the event: no second reader.
    assert len(program.asked) == 1

    assert outcome.kind == "written"
    path = folder / "2026-11-24-fed-holds-taiex-rises.md"
    assert outcome.path == path
    text = path.read_text(encoding="utf-8")
    front = yaml.safe_load(text.split("---\n")[1])
    assert list(front) == [
        "title",
        "event_date",
        "targets",
        "markets",
        "tickers",
        "exposure",
        "significance",
        "keyword_groups",
        "sources",
    ]
    assert [source["id"] for source in front["sources"]] == ["s1", "s2", "d1"]
    s1, s2 = front["sources"][:2]
    assert (s1["url"], s1["published"], s1["lang"], s1["format"]) == (
        FED.url,
        FED.published,
        "en",
        "html",
    )
    assert (s2["url"], s2["published"], s2["publisher"]) == (
        CNA.url,
        "unknown",
        "中央社",
    )
    assert 'tickers: ["2330"]' in text and "targets: [2, 1]" in text
    assert text.count("    accessed: 2026-11-26\n") == 2 and "&id" not in text
    assert _sections(text) == [
        "## 事件發生",
        "## 影響股市證據",
        "## 相關標的",
        "## 當日與之後的行情",
        "## 後續與不同說法",
    ]
    # The source mark right after a full-width full stop, one space after anything else.
    assert "- 台積電上漲3%。[s2]\n" in text
    assert (
        "- The Federal Reserve kept its benchmark rate at 3.75% to 4% on Wednesday. [s1]\n"
        in text
    )
    assert "passage" not in text and "新台幣1兆2129.57億元" not in text
    assert text.endswith("> significance 依據（supporting）：測試用的事件。\n")
    assert "| 加權指數 | 2026-11-24 |" in text
    assert conversions.read_text(encoding="utf-8").endswith(
        "| 2026-11-24-fed-holds-taiex-rises | 新台幣1兆2129.57億元 | NT$1.212957 trillion | 成交值 |\n"
    )


def test_an_empty_section_has_its_note_and_an_uncited_source_is_left_out(
    tmp_path: Path,
) -> None:
    def only_the_fed(made: dict[str, Any]) -> None:
        sections = made["sections"]
        sections[1]["items"], sections[2]["items"] = [], []
        sections[1]["notes"] = ["本檔讀過的來源沒有記載股市變動。"]
        sections[2]["notes"] = ["本檔讀過的來源沒有點名個別標的。"]
        made["title"] = "聯準會利率維持不變"
        made["conversions"] = []

    outcome = _make(tmp_path, Program([record(only_the_fed)]))

    assert outcome.path is not None
    text = outcome.path.read_text(encoding="utf-8")
    assert (
        "## 影響股市證據\n\n> 本檔讀過的來源沒有記載股市變動。\n\n## 相關標的" in text
    )
    front = yaml.safe_load(text.split("---\n")[1])
    assert [source["url"] for source in front["sources"][:-1]] == [FED.url]


def _passage_elsewhere(made: dict[str, Any]) -> None:
    made["sections"][2]["items"][0]["passage"] = "台積電下跌5%"


def _wrong_language(made: dict[str, Any]) -> None:
    made["sections"][2]["items"][0]["text"] = "TSMC rose 3%."


def _unknown_word(made: dict[str, Any]) -> None:
    made["exposure"] = ["fed_policy", "crypto"]


def _unlisted_target(made: dict[str, Any]) -> None:
    made["targets"] = [9]


def _unlisted_market(made: dict[str, Any]) -> None:
    made["markets"] = ["JP"]


def _unconverted(made: dict[str, Any]) -> None:
    made["sections"][1]["items"][0]["text"] = "成交值新台幣1兆2129.57億元。"


def _stop_inside_quote(made: dict[str, Any]) -> None:
    made["sections"][0]["items"][0]["text"] = (
        'The Fed: "The Federal Reserve kept its benchmark rate at 3.75% to 4% on Wednesday."'
    )


def _stop_inside_chinese_quote(made: dict[str, Any]) -> None:
    made["sections"][2]["items"][0]["text"] = "中央社：「台積電上漲3%。」"


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (_passage_elsewhere, "相關標的 item 1: its passage is not in the text of s2"),
        (_wrong_language, "相關標的 item 1 is not in the language of s2 (zh-TW)"),
        (_unknown_word, "exposure words not in the vocabulary: crypto"),
        (_unlisted_target, "targets must be one or more of [1, 2, 3, 4, 5]"),
        (_unlisted_market, "markets must be one or more of"),
        (
            _unconverted,
            "影響股市證據 item 1 still writes a quantity with 萬, 億, 兆 or 碼",
        ),
        (
            _stop_inside_quote,
            "事件發生 item 1 ends with its full stop inside the quotation marks",
        ),
        (
            _stop_inside_chinese_quote,
            "相關標的 item 1 ends with its full stop inside the quotation marks",
        ),
    ],
)
def test_a_record_that_breaks_a_rule_twice_is_not_written(
    tmp_path: Path, change: Any, reason: str
) -> None:
    told: list[str] = []
    program = Program([record(change), record(change)])

    outcome = _make(tmp_path, program, told=told)

    assert outcome.kind == "refused"
    assert not list(tmp_path.iterdir())
    assert sum(reason in line for line in told) == 2
    # Asked once more with the reasons.
    assert len(program.asked) == 2
    assert reason in program.asked[1][1] and "<earlier_record>" in program.asked[1][1]


def test_a_name_such_as_兆豐金_is_not_a_quantity(tmp_path: Path) -> None:
    def name(made: dict[str, Any]) -> None:
        made["sections"][2]["items"].append(
            {"text": "兆豐金也走高。", "source": "s2", "passage": "兆豐金也走高"}
        )

    assert _make(tmp_path, Program([record(name)])).kind == "written"


def test_a_quotation_with_its_full_stop_outside_is_written(tmp_path: Path) -> None:
    def quoted(made: dict[str, Any]) -> None:
        made["sections"][0]["items"][0]["text"] = (
            'The Fed: "The Federal Reserve kept its benchmark rate at 3.75% to 4% on '
            'Wednesday".'
        )
        made["sections"][2]["items"][0]["text"] = "中央社：「台積電上漲3%」。"

    outcome = _make(tmp_path, Program([record(quoted)]))

    assert outcome.path is not None
    text = outcome.path.read_text(encoding="utf-8")
    assert 'on Wednesday". [s1]\n' in text and "「台積電上漲3%」。[s2]\n" in text


def test_the_agent_is_given_each_markets_close_for_event_time(tmp_path: Path) -> None:
    program = Program([record()])

    _make(tmp_path, program)

    system_prompt = program.asked[0][0]
    assert "<markets>\nUS 美股: closes 16:00 America/New_York\n" in system_prompt
    assert "TW 台股: closes 13:30 Asia/Taipei\n</markets>" in system_prompt


def test_a_record_refused_once_is_written_when_asked_again(tmp_path: Path) -> None:
    program = Program([record(_unknown_word), record()])

    assert _make(tmp_path, program).kind == "written"
    assert len(program.asked) == 2


def test_a_failed_run_refuses_the_event_and_names_why(tmp_path: Path) -> None:
    program = Program([ProgramError("Claude Code exited with code 1")])

    outcome = _make(tmp_path, program)

    assert (outcome.kind, outcome.detail) == (
        "refused",
        "the writing: Claude Code exited with code 1",
    )


def test_a_run_stopped_part_way_leaves_no_half_file_and_resumes_without_doubles(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "truth"
    conversions = tmp_path / "number_conversions.md"
    conversions.write_text("", encoding="utf-8")
    other = "https://www.federalreserve.gov/newsevents/b.htm"
    second = (replace(FED, asked=other, url=other),)

    def stop(input_text: str) -> dict[str, Any]:
        raise KeyboardInterrupt

    first_run = maker(folder, Program([record(), stop]), conversions=conversions)

    async def run_both() -> None:
        await make(first_run)
        await make(first_run, second, "The Fed again")

    with pytest.raises(KeyboardInterrupt):
        asyncio.run(run_both())
    written = sorted(path.name for path in folder.iterdir())
    assert written == ["2026-11-24-fed-holds-taiex-rises.md"]
    assert not list(folder.glob(f"*{PART_SUFFIX}"))
    rows_after_first = conversions.read_text(encoding="utf-8")

    again = maker(folder, Program([]), conversions=conversions)
    again.existing = folder_events(folder, None)
    outcome = asyncio.run(make(again))

    assert (outcome.kind, outcome.detail) == (
        "unchanged",
        "the folder has it: 2026-11-24-fed-holds-taiex-rises.md",
    )
    assert conversions.read_text(encoding="utf-8") == rows_after_first
    assert rows_after_first.count("新台幣1兆2129.57億元") == 1


def test_an_event_the_folder_has_under_other_pages_is_not_written_again(
    tmp_path: Path,
) -> None:
    held = tmp_path / "2026-11-24-taiex-surges.md"
    held.write_text(
        "---\ntitle: 加權指數大漲\nsources:\n  - id: s1\n    url: https://other.example/a\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "2026-11-23-other-day.md").write_text(
        "---\ntitle: 前一天的事\nsources: []\n---\n", encoding="utf-8"
    )
    program = Program([record(lambda made: made.update(same_as=held.name))])
    built = maker(tmp_path, program)
    built.existing = folder_events(tmp_path, None)

    outcome = asyncio.run(make(built))

    assert (outcome.kind, outcome.detail) == (
        "unchanged",
        "the folder has it: 2026-11-24-taiex-surges.md",
    )
    _, question, schema = program.asked[0]
    # Only the files of the event's date are listed, and only they can be named.
    assert "2026-11-24-taiex-surges.md  加權指數大漲" in question
    assert "前一天的事" not in question
    assert schema["properties"]["same_as"]["enum"] == [held.name, None]
    assert len(program.asked) == 1


def test_a_taken_name_gets_a_number(tmp_path: Path) -> None:
    (tmp_path / "2026-11-24-fed-holds-taiex-rises.md").write_text("x", encoding="utf-8")

    outcome = _make(tmp_path, Program([record()]))

    assert outcome.path == tmp_path / "2026-11-24-fed-holds-taiex-rises-2.md"


def test_an_event_outside_the_asked_dates_is_not_written(tmp_path: Path) -> None:
    def later(made: dict[str, Any]) -> None:
        made["event_date"] = "2026-11-27"

    outcome = _make(tmp_path, Program([record(later), record(later)]))

    assert outcome.kind == "refused"
    assert not list(tmp_path.iterdir())
