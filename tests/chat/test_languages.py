"""The service's own texts in each language, without searching or starting a model."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from chat_bridge.chat import service
from chat_bridge.chat.schemas import ChatDelta
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.ingest.service import MARKET_SECTION


@pytest.mark.parametrize(
    ("question", "language"),
    [
        pytest.param("聯準會降息了嗎？", "zh-TW", id="Chinese"),
        pytest.param("Did the Fed cut rates?", "en", id="English"),
        pytest.param("TSMC 法說會說了什麼", "zh-TW", id="mixed"),
        pytest.param("qzxv 12345", "en", id="no Han character"),
    ],
)
def test_a_question_with_a_han_character_is_chinese(
    question: str, language: str
) -> None:
    assert service.question_language(question) == language


async def _fixed_reply(question: str) -> list[ChatDelta]:
    return [delta async for delta in service.answer_stream(question, [])]


@pytest.mark.parametrize(
    ("question", "reply"),
    [
        pytest.param("2022 年世界盃冠軍是誰？", "資料裡沒有相關內容。", id="Chinese"),
        pytest.param(
            "Who won the 2022 World Cup?", "The data has nothing on this.", id="English"
        ),
    ],
)
def test_the_fixed_reply_is_in_the_language_of_the_question_only(
    monkeypatch: pytest.MonkeyPatch, question: str, reply: str
) -> None:
    async def no_record(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(service, "_record", no_record)

    context, answer = asyncio.run(_fixed_reply(question))

    assert answer.delta == reply
    assert context.context is not None
    assert context.context.disclaimer == service.DISCLAIMER


def test_the_notice_is_one_text_per_language() -> None:
    assert "investment advice" not in service.DISCLAIMER["zh-TW"]
    assert service.question_language(service.DISCLAIMER["en"]) == "en"


def test_only_the_fixed_section_names_are_given_in_both_languages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def hit(section_id: int, heading: str) -> SimpleNamespace:
        return SimpleNamespace(
            section_id=section_id,
            source_path="data/truth/a.md",
            title="T",
            heading=heading,
            event_date=date(2026, 9, 17),
            markets=(),
            event_time=None,
            content="text",
            score=0.03,
        )

    async def search(question: str, limit: int, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            hits=[hit(1, "影響股市證據"), hit(2, "My own heading"), hit(3, "Page 3")]
        )

    monkeypatch.setattr(service, "search", search)

    sources = [found.source for found in asyncio.run(service.find_sections("q"))]

    assert sources[0].heading == "影響股市證據"
    assert sources[0].heading_localizations == {
        "zh-TW": "影響股市證據",
        "en": "Evidence of market impact",
    }
    assert sources[1].heading_localizations is None
    # A PDF page's heading is not translated: its page label is not stored apart from it.
    assert sources[2].heading_localizations is None


def test_every_stored_section_name_of_the_sample_news_is_in_the_table() -> None:
    names = {
        line.removeprefix("## ").strip()
        for path in PROJECT_ROOT.joinpath("data", "truth").glob("*.md")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    }

    # The market section is not stored, so no page shows its name.
    assert names - {MARKET_SECTION} == set(service.SECTION_NAMES)
