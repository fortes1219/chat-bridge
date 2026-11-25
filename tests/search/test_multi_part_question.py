"""The six-part question on the 71 sample files: each part reaches the model, and nothing the
question's own search finds is dropped.

The parts are those split from the question's own wording, and, once the real runs have been
recorded, those each program listed. No model is started. Ingesting the sample files takes
minutes, so these tests are marked slow.
"""

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from chat_bridge.chat import service
from chat_bridge.search.service import latest_event_date, search, search_many

pytestmark = pytest.mark.slow

CASE: dict[str, Any] = json.loads(
    (Path(__file__).parents[1] / "data" / "multi_part_question.json").read_text(
        encoding="utf-8"
    )
)
MARKET = CASE["market_heading"]
SAMPLE_LATEST_EVENT_DATE = date(2026, 11, 17)


def _part_lists() -> list[Any]:
    lists = [
        pytest.param(language, parts, id=f"wording-{language}")
        for language, parts in CASE["parts_from_wording"].items()
    ]
    lists += [
        pytest.param(language, parts, id=f"{program}-{language}")
        for program, by_language in CASE["parts_from_real_runs"].items()
        for language, parts in by_language.items()
    ]
    return lists


@pytest.mark.parametrize(("language", "parts"), _part_lists())
def test_each_part_reaches_the_model_and_nothing_the_question_finds_is_lost(
    sample_knowledge_base: None, language: str, parts: list[str]
) -> None:
    question = CASE["questions"][language]

    async def run() -> tuple[
        list[str], list[service.FoundSection], list[service.FoundSection]
    ]:
        # The question's search as it ran before parts were searched.
        kept = await search(question, service.KEPT_SECTIONS)
        own = await service.find_sections(question)
        gathered, _ = await service.gather_sections(question, own, parts)
        return [f"{h.source_path}#{h.heading}" for h in kept.hits], own, gathered

    kept, own, gathered = asyncio.run(run())

    def stem(section: service.FoundSection) -> str:
        return Path(section.source.file).stem

    news = {stem(s) for s in gathered if s.source.heading != MARKET}
    market = {stem(s) for s in gathered if s.source.heading == MARKET}
    found = {
        part: sorted(news & set(core)) for part, core in CASE["core_files"].items()
    }
    market_core = set().union(*(CASE["core_files"][p] for p in CASE["market_from"]))
    print(
        language,
        len(gathered),
        "sections;",
        found,
        "0050:",
        sorted(market & market_core),
    )

    assert [part for part, files in found.items() if not files] == []
    assert market & market_core, "no market section for the 0050 part"
    assert {s.section_id for s in own} <= {s.section_id for s in gathered}
    assert [s.source.number for s in gathered] == list(range(1, len(gathered) + 1))
    # Nothing the question's own search found is crowded out: it comes first, whole, in order.
    assert [
        f"{s.source.file}#{s.source.heading}" for s in gathered[: len(kept)]
    ] == kept
    # After it, market sections do not rank: they come last, each with a document found by a
    # news section.
    rest = gathered[len(kept) :]
    headings = [s.source.heading for s in rest]
    first_market = headings.index(MARKET)
    assert all(heading == MARKET for heading in headings[first_market:])
    news_found = {stem(s) for s in gathered if s.source.heading != MARKET}
    assert {stem(s) for s in rest[first_market:]} <= news_found


def test_several_queries_in_one_session_find_what_each_finds_alone(
    sample_knowledge_base: None,
) -> None:
    queries = CASE["parts_from_wording"]["zh-TW"][:3]

    together = asyncio.run(search_many(queries, 8))
    alone = [asyncio.run(search(query, 8)) for query in queries]

    for one, other in zip(together, alone, strict=True):
        assert one.query == other.query
        assert [h.section_id for h in one.hits] == [h.section_id for h in other.hits]


def test_the_data_reaches_the_sample_news_latest_event_date(
    sample_knowledge_base: None,
) -> None:
    assert asyncio.run(latest_event_date()) == SAMPLE_LATEST_EVENT_DATE
