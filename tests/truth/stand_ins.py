"""A two-source event, a record the agent could answer for it, and a stand-in program: what the
tests of making truth files share. No network, no program started."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from chat_bridge.collect.closes import SeriesCloses
from chat_bridge.collect.pages import Page
from chat_bridge.truth.maker import EventOutcome, Maker
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import read_rules
from tests.collect.test_moves import LISTED, SP500_CLOSES, TAIEX_CLOSES

NOW = datetime(2026, 11, 26, 6, 0, tzinfo=UTC)
# The date the search or the sorting gave the event, and the dates it was asked for.
FOUND_DATE = date(2026, 11, 24)
WINDOW = Window(date(2026, 11, 18), date(2026, 11, 25))
ABOUT = "The Fed holds rates; the TAIEX rises"
FED = Page(
    asked="https://www.federalreserve.gov/newsevents/a.htm",
    url="https://www.federalreserve.gov/newsevents/a.htm",
    title="Federal Reserve issues FOMC statement",
    site="Board of Governors of the Federal Reserve System",
    text=(
        "The Federal Reserve kept its benchmark rate at 3.75% to 4% on Wednesday.\n"
        "Officials said further   increases may be needed if inflation stays high."
    ),
    published=date(2026, 11, 24),
)
CNA = Page(
    asked="https://www.cna.com.tw/news/afe/1.aspx",
    url="https://www.cna.com.tw/news/afe/1.aspx",
    title="台股大漲",
    site="中央社",
    text="台股今天上漲，加權指數收40122.35點，成交值新台幣1兆2129.57億元。\n台積電上漲3%，兆豐金也走高。",
    published=None,
)
PAGES = (FED, CNA)

RECORD: dict[str, Any] = {
    "same_as": None,
    "title": "聯準會利率維持不變，加權指數收40122.35點",
    "slug": "fed-holds-taiex-rises",
    "event_date": "2026-11-24",
    "event_time": None,
    "targets": [2, 1],
    "markets": ["TW"],
    "tickers": ["2330"],
    "exposure": ["fed_policy", "tw_equity_broad"],
    "significance": "supporting",
    "significance_reason": "測試用的事件。",
    "keyword_groups": [["聯準會", "Fed"], ["加權指數", "TAIEX"]],
    "sources": [
        {"id": "s1", "publisher": "Federal Reserve", "lang": "en"},
        {"id": "s2", "publisher": "中央社", "lang": "zh-TW"},
    ],
    "sections": [
        {
            "heading": "事件發生",
            "items": [
                {
                    "text": "The Federal Reserve kept its benchmark rate at 3.75% to 4% on Wednesday.",
                    "source": "s1",
                    "passage": "The Federal Reserve kept its benchmark rate at 3.75% to 4% on Wednesday.",
                }
            ],
            "notes": [],
        },
        {
            "heading": "影響股市證據",
            "items": [
                {
                    "text": "加權指數收40122.35點，成交值 NT$1.212957 trillion。",
                    "source": "s2",
                    "passage": "加權指數收40122.35點，成交值新台幣1兆2129.57億元",
                }
            ],
            "notes": [],
        },
        {
            "heading": "相關標的",
            "items": [
                {
                    "text": "台積電上漲3%。",
                    "source": "s2",
                    "passage": "台積電上漲3%",
                }
            ],
            "notes": [],
        },
        {
            "heading": "後續與不同說法",
            "items": [
                {
                    "text": "Officials said further increases may be needed if inflation stays high.",
                    "source": "s1",
                    "passage": "Officials said further increases may be needed if inflation stays high.",
                }
            ],
            "notes": [],
        },
    ],
    "conversions": [
        {
            "source": "s2",
            "original": "新台幣1兆2129.57億元",
            "converted": "NT$1.212957 trillion",
            "note": "成交值",
        }
    ],
}


def record(change: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """The record, with a change made to a copy of it."""
    made = copy.deepcopy(RECORD)
    if change is not None:
        change(made)
    return made


@dataclass
class Program:
    """A stand-in program: each run answers with the next of `answers`; a function answer is
    called with what the run was given."""

    answers: list[Any]
    asked: list[tuple[str, str, dict[str, Any]]] = field(default_factory=list)

    async def reply_in_shape(
        self,
        system_prompt: str,
        input_text: str,
        schema: dict[str, Any],
        *,
        on_start: Callable[[list[str]], None],
    ) -> dict[str, Any]:
        self.asked.append((system_prompt, input_text, schema))
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            result: dict[str, Any] = answer(input_text)
            return result
        made: dict[str, Any] = answer
        return made


def closes() -> dict[str, SeriesCloses]:
    return {
        "^TWII": SeriesCloses(
            closes={date(2026, 11, day): close for day, close in TAIEX_CLOSES.items()}
        ),
        "^GSPC": SeriesCloses(
            closes={date(2026, 11, day): close for day, close in SP500_CLOSES.items()}
        ),
    }


def maker(folder: Path, program: Program, *, conversions: Path | None = None) -> Maker:
    return Maker(
        rules=read_rules(),
        folder=folder,
        program=program,  # type: ignore[arg-type]
        name="Claude Code",
        closes=closes(),
        listed=LISTED,
        now=NOW,
        example=None,
        conversions_file=conversions,
    )


async def make(
    built: Maker,
    pages: tuple[Page, ...] = PAGES,
    about: str = ABOUT,
    told: list[str] | None = None,
) -> EventOutcome:
    """The event of FOUND_DATE made with `built`, what it tells going to `told`."""
    return await built.make(
        about,
        FOUND_DATE,
        pages,
        WINDOW,
        told.append if told is not None else lambda line: None,
    )
