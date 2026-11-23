"""Every question is recorded, and the ones the search found nothing for can be listed alone.

The knowledge base is two sample files with the real embedding model and the embedded database,
so the tests are marked slow. Claude Code is made to look missing, so no test ever starts the
model, wherever the tests run.
"""

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest

from chat_bridge.chat import claude_code, service
from chat_bridge.chat.claude_code import Login
from chat_bridge.chat.schemas import ChatDelta
from tests.utils import copy_sample_files, ingest, prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

SAMPLE_FILES = (
    "2026-06-15-nvidia-25-billion-bond.md",
    "2026-11-12-goldman-sees-sp500-8700.md",
)
# Words that are in no sample file and mean nothing, so neither search method finds them.
NOTHING_TO_FIND = "qzxv wplkj"
# Words from a sample file's title, so the search finds that file.
SOMETHING_TO_FIND = "輝達 發債"


@pytest.fixture
def knowledge_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    def missing() -> str:
        raise claude_code.ClaudeCodeError("Claude Code is not installed")

    monkeypatch.setattr(claude_code, "find_executable", missing)
    folder = copy_sample_files(tmp_path / "truth", SAMPLE_FILES)
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        ingest(folder)
        yield


async def _ask(question: str) -> tuple[list[ChatDelta], Exception | None]:
    """Ask as the chat endpoint does: search first, then read the stream to its end."""
    sections = await service.find_sections(question)
    deltas: list[ChatDelta] = []
    try:
        async for delta in service.answer_stream(question, sections):
            deltas.append(delta)
    except Exception as error:
        return deltas, error
    return deltas, None


def test_a_question_the_data_cannot_answer_gets_the_fixed_reply(
    knowledge_base: None,
) -> None:
    deltas, error = asyncio.run(_ask(NOTHING_TO_FIND))

    assert error is None
    context, reply = deltas
    assert context.context is not None
    assert context.context.sources == []
    assert context.context.disclaimer == service.DISCLAIMER
    assert reply.delta == service.NOT_IN_DATA["en"]


def test_every_question_is_recorded_and_only_the_unanswered_are_listed(
    knowledge_base: None,
) -> None:
    asyncio.run(_ask(NOTHING_TO_FIND))
    deltas, error = asyncio.run(_ask(SOMETHING_TO_FIND))

    # With Claude Code missing, the found sources still go out first, then the stream stops.
    assert isinstance(error, service.NoLoginError)
    assert str(error) == service.NO_LOGIN_MESSAGES[Login.NOT_INSTALLED]
    assert deltas[0].context is not None
    assert deltas[0].context.sources

    every = asyncio.run(service.list_records(unanswered=False, limit=10))
    unanswered = asyncio.run(service.list_records(unanswered=True, limit=10))

    assert [record.question for record in every] == [SOMETHING_TO_FIND, NOTHING_TO_FIND]
    assert [record.question for record in unanswered] == [NOTHING_TO_FIND]
    found = every[0].details
    assert found["sections"]
    assert all(section["section_id"] for section in found["sections"])
    assert found["sent_to_model"] is None
    assert found["command_line"] is None
    assert found["error"] == service.NO_LOGIN_MESSAGES[Login.NOT_INSTALLED]
