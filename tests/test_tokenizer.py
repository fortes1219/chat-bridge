"""How a question becomes keyword clauses, and how the dictionary download is checked."""

import urllib.request
from pathlib import Path
from typing import Any

import pytest

from chat_bridge.config import LOCAL_DATA_ENV
from chat_bridge.synonyms import Synonyms, load_synonyms
from chat_bridge.tokenizer import (
    DICTIONARY_SIZE,
    DictionaryError,
    SearchTokenizer,
    build_tokenizer,
    ensure_dictionary,
    query_clauses,
)

# Keyword names from the sample data that the questions below use.
KEYWORD_NAMES = ("AI", "台積電", "法說會", "費半")


@pytest.fixture(scope="module")
def synonyms() -> Synonyms:
    return load_synonyms()


@pytest.fixture(scope="module")
def tokenizer(synonyms: Synonyms) -> SearchTokenizer:
    return build_tokenizer([*KEYWORD_NAMES, *synonyms.names()])


def lowered(clauses: list[str]) -> set[str]:
    return {clause.lower() for clause in clauses}


# ---------------------------------------------------------------- Query clauses


def test_english_user_word_matches_only_a_whole_word(
    tokenizer: SearchTokenizer,
) -> None:
    assert "ai" not in lowered(query_clauses(tokenizer, "Did the Fed raise rates?"))
    assert "ai" in lowered(query_clauses(tokenizer, "Is AI spending a bubble?"))


def test_english_stop_words_are_dropped(tokenizer: SearchTokenizer) -> None:
    clauses = lowered(query_clauses(tokenizer, "Who won the Super Bowl?"))

    assert clauses.isdisjoint({"who", "the"})
    assert {"won", "super", "bowl"} <= clauses


def test_question_words_come_before_their_synonyms(
    tokenizer: SearchTokenizer, synonyms: Synonyms
) -> None:
    question = "費半"
    clauses = query_clauses(tokenizer, question, synonyms.expand(question))

    assert clauses[0] == "費半"
    assert {"費城半導體指數", "SOX"} <= set(clauses)


def test_a_run_of_single_han_characters_becomes_one_clause(
    tokenizer: SearchTokenizer,
) -> None:
    clauses = query_clauses(tokenizer, "台積電法說會說了什麼")

    assert clauses[:2] == ["台積電", "法說會"]
    assert "說 了" in clauses


def test_a_question_without_searchable_words_has_no_clauses(
    tokenizer: SearchTokenizer,
) -> None:
    assert query_clauses(tokenizer, "？？ !!") == []


# ------------------------------------------------------------ Dictionary download


class FakeResponse:
    """Stands in for urlopen's response; records how many bytes were asked for."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.asked: int | None = None

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        self.asked = size
        return self.data[:size]


@pytest.fixture
def empty_local_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(LOCAL_DATA_ENV, str(tmp_path))
    return tmp_path


def serve(monkeypatch: pytest.MonkeyPatch, response: Any) -> None:
    def urlopen(*_: object, **__: object) -> Any:
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)


def assert_nothing_saved(folder: Path) -> None:
    assert list((folder / "jieba").iterdir()) == []


def test_a_larger_download_is_refused_after_one_byte_past_the_pinned_size(
    empty_local_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse(b"x" * (DICTIONARY_SIZE + 100))
    serve(monkeypatch, response)

    with pytest.raises(DictionaryError, match="larger than the pinned file"):
        ensure_dictionary()

    assert response.asked == DICTIONARY_SIZE + 1
    assert_nothing_saved(empty_local_data)


def test_a_download_with_other_content_is_refused(
    empty_local_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(monkeypatch, FakeResponse(b"x" * DICTIONARY_SIZE))

    with pytest.raises(DictionaryError, match="does not match the pinned file"):
        ensure_dictionary()

    assert_nothing_saved(empty_local_data)


def test_a_failed_download_is_reported_without_a_fallback(
    empty_local_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(monkeypatch, OSError("network is unreachable"))

    with pytest.raises(DictionaryError, match="Could not download"):
        ensure_dictionary()

    assert_nothing_saved(empty_local_data)
