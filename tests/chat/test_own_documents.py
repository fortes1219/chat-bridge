"""What the chat says when the knowledge base holds someone's own documents: the sample questions
only while the sample news is stored, and no instruction or notice that calls the documents market
news or public data. No database is read: whether the sample news is stored is a stand-in."""

from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat import samples, service
from chat_bridge.chat.server import create_app
from chat_bridge.ingest import service as ingest_service
from chat_bridge.strategy import revision

INSTRUCTION_FILES = (
    Path(service.__file__).with_name("answer_prompt.md"),
    Path(service.__file__).with_name("split_prompt.md"),
    Path(revision.__file__).with_name("revision_prompt.md"),
)


@pytest.fixture
def asked(monkeypatch: pytest.MonkeyPatch) -> list[Sequence[str]]:
    """The paths each check for stored documents was given; the sample news is stored."""
    made: list[Sequence[str]] = []

    async def holds_any(paths: Sequence[str]) -> bool:
        made.append(paths)
        return True

    monkeypatch.setattr(ingest_service, "holds_any", holds_any)
    return made


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def test_the_sample_questions_file_has_every_question_in_both_languages() -> None:
    questions = samples.sample_questions_file()

    assert len(questions) >= 1
    assert all(set(question) == {"zh-TW", "en"} for question in questions)


def test_the_sample_news_paths_are_the_files_of_the_sample_folder() -> None:
    paths = samples.sample_news_paths()

    assert len(paths) == len(list(samples.SAMPLE_NEWS.glob("*.md")))
    assert all("/" not in path and path.endswith(".md") for path in paths)


def test_the_questions_are_offered_while_the_sample_news_is_stored(
    client: TestClient, asked: list[Sequence[str]]
) -> None:
    response = client.get("/chat/samples")

    assert response.status_code == 200
    assert response.json()["questions"] == list(samples.sample_questions_file())
    assert list(asked[0]) == list(samples.sample_news_paths())


def test_no_question_is_offered_once_the_sample_news_is_gone(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def holds_none(paths: Sequence[str]) -> bool:
        return False

    monkeypatch.setattr(ingest_service, "holds_any", holds_none)

    response = client.get("/chat/samples")

    assert response.json() == {"questions": []}


def test_a_sample_questions_file_not_in_both_languages_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broken = tmp_path / "sample_questions.json"
    broken.write_text(
        '{"about": "x", "questions": [{"zh-TW": "只有中文"}]}', encoding="utf-8"
    )
    monkeypatch.setattr(samples, "SAMPLE_QUESTIONS_FILE", broken)
    samples.sample_questions_file.cache_clear()
    try:
        with pytest.raises(samples.SampleQuestionsFileError, match="both languages"):
            samples.sample_questions_file()
    finally:
        samples.sample_questions_file.cache_clear()


@pytest.mark.parametrize("path", INSTRUCTION_FILES, ids=lambda path: path.name)
def test_no_instruction_calls_the_knowledge_base_market_news(path: Path) -> None:
    text = path.read_text(encoding="utf-8").lower()

    assert "market news" not in text
    assert "market events" not in text


def test_the_notice_names_the_documents_not_public_data() -> None:
    assert "公開資料" not in service.DISCLAIMER["zh-TW"]
    assert "public data" not in service.DISCLAIMER["en"]
    assert "知識庫" in service.DISCLAIMER["zh-TW"]
    assert "knowledge base" in service.DISCLAIMER["en"]
