"""A news file read for its section, and the section and data sources written back."""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from chat_bridge.collect import news_files
from chat_bridge.collect.markets import market_series
from chat_bridge.collect.moves import HEADING, Section
from chat_bridge.collect.news_files import NewsFileError
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.ingest.sections import parse_markdown

SAMPLE_NEWS = PROJECT_ROOT / "data" / "truth"
LISTED = market_series()
SYMBOLS = [one.symbol for one in LISTED.series]
ACCESSED = datetime(2026, 11, 26, 6, 0, tzinfo=UTC)
FRONT = """---
title: 測試事件
event_date: 2026-11-24
{event_time}markets: [TW, US]
keyword_groups:
  - [台股]
sources:
  - id: s1
    url: https://example.com/a
    publisher: Example
    published: 2026-11-24
    accessed: 2026-11-25
    lang: zh-TW
    format: html
---
"""
BODY = """
## 事件發生

- 台股大漲。[s1]

## 影響股市證據

> 本檔讀過的來源沒有寫。

## 相關標的

> 本檔讀過的來源沒有點名個別標的。
{later}
> significance 依據（supporting）：測試。
"""
LATER = """
## 後續與不同說法

- 之後的看法。[s1]
"""


def _write(tmp_path: Path, event_time: str = "", later: str = LATER) -> Path:
    path = tmp_path / "2026-11-24-test.md"
    text = FRONT.format(event_time=event_time) + BODY.format(later=later)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _section(rows: str = "| 加權指數 | x |", uses_backup: bool = False) -> Section:
    return Section(
        (f"## {HEADING}", "", "> 第一行", "", "| 序列 | 註 |", "|---|---|", rows),
        uses_backup,
    )


@pytest.mark.parametrize("path", sorted(SAMPLE_NEWS.glob("*.md")), ids=lambda p: p.name)
def test_the_round_trip_gives_back_every_sample_files_front_matter(path: Path) -> None:
    front = path.read_text(encoding="utf-8").split("---\n", 2)[1]

    assert news_files.round_trip(front) == front


def test_a_section_is_added_before_the_later_views(tmp_path: Path) -> None:
    news = news_files.read(_write(tmp_path), LISTED)

    text = news_files.with_section(news, _section(), ACCESSED, SYMBOLS)

    assert text is not None
    assert (
        text.index("## 相關標的")
        < text.index(f"## {HEADING}")
        < text.index("## 後續與不同說法")
    )
    assert "  - id: d1\n" in text and "accessed: 2026-11-26T06:00:00+00:00" in text
    assert "  - id: d2\n" not in text


def test_without_later_views_a_section_is_added_before_the_closing_line(
    tmp_path: Path,
) -> None:
    news = news_files.read(_write(tmp_path, later=""), LISTED)

    text = news_files.with_section(news, _section(), ACCESSED, SYMBOLS)

    assert text is not None
    assert text.index(f"## {HEADING}") < text.index("> significance 依據")
    assert text.endswith("> significance 依據（supporting）：測試。\n")


def test_a_section_is_replaced_and_a_note_below_its_table_is_kept(
    tmp_path: Path,
) -> None:
    sample = SAMPLE_NEWS / "2026-11-16-bis-remote-access-chip-rule.md"
    path = tmp_path / sample.name
    path.write_bytes(sample.read_bytes())
    original = path.read_text(encoding="utf-8")
    news = news_files.read(path, LISTED)

    text = news_files.with_section(news, _section(uses_backup=True), ACCESSED, SYMBOLS)

    assert text is not None
    assert "| 加權指數 | x |" in text and "| 加權指數 | 2026-11-17 |" not in text
    assert (
        "> 規則的生效日與意見徵詢期，新聞稿頁面沒有寫；Federal Register 文件沒有開。"
        in text
    )
    assert "  - id: d2\n" in text
    # Before the section, only the data sources changed.
    head = original.split(f"## {HEADING}")[0]
    new_head = text.split(f"## {HEADING}")[0]
    assert head.split("  - id: d1")[0] == new_head.split("  - id: d1")[0]


def test_a_section_the_same_as_the_files_leaves_the_file_as_it_was() -> None:
    sample = SAMPLE_NEWS / "2026-11-16-bis-remote-access-chip-rule.md"
    news = news_files.read(sample, LISTED)
    start = news.lines.index(f"## {HEADING}")
    end = next(
        number
        for number in range(start + 6, len(news.lines))
        if not news.lines[number].startswith("| ")
    )

    same = Section(tuple(news.lines[start:end]), False)

    assert news_files.with_section(news, same, ACCESSED, SYMBOLS) is None


@pytest.mark.parametrize(
    ("event_time", "reason"),
    [
        ("event_time: 2026-11-24T13:30:00\n", "no offset"),
        ("event_time: '24 Nov 2026 13:30'\n", "not an ISO 8601 time"),
        ("event_time: 2026-11-23T23:30:00+08:00\n", "another day"),
    ],
)
def test_an_event_time_that_cannot_be_used_refuses_the_file(
    tmp_path: Path, event_time: str, reason: str
) -> None:
    with pytest.raises(NewsFileError, match=reason):
        news_files.read(_write(tmp_path, event_time), LISTED)


def test_an_event_time_with_its_offset_is_the_moment(tmp_path: Path) -> None:
    news = news_files.read(
        _write(tmp_path, "event_time: 2026-11-24T13:30:00+08:00\n"), LISTED
    )

    assert news.event.moment is not None
    assert news.event.moment.isoformat() == "2026-11-24T13:30:00+08:00"


def test_a_file_without_markets_is_refused(tmp_path: Path) -> None:
    path = _write(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace("markets: [TW, US]\n", ""),
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(NewsFileError, match="no markets"):
        news_files.read(path, LISTED)


def test_a_file_with_event_time_is_read_by_ingest_as_one_without_it(
    tmp_path: Path,
) -> None:
    with_time = _write(tmp_path, "event_time: 2026-11-24T13:30:00+08:00\n").read_text(
        encoding="utf-8"
    )
    without = FRONT.format(event_time="") + BODY.format(later=LATER)

    read_with, read_without = (
        parse_markdown(text, "fallback") for text in (with_time, without)
    )

    assert read_with == read_without
    assert read_with.event_date == date(2026, 11, 24)
