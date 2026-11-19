"""jieba tokenization shared by indexing and searching.

This follows MaxKB: jieba splits the text in Python, the words are joined with spaces,
and PostgreSQL stores them as a tsvector with the `simple` configuration. Indexing and
searching use the same tokenizer, including the same user words.
"""

import hashlib
import logging
import re
import urllib.request
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jieba

from chat_bridge.config import local_data_dir
from chat_bridge.errors import LocalSetupError

# The Traditional Chinese dictionary from the jieba repository, pinned to one commit.
# The file is checked by size and by its git blob hash, so a partial or changed file is refused.
DICTIONARY_URL = (
    "https://raw.githubusercontent.com/fxsjy/jieba/"
    "67fa2e36e72f69d9134b8a1037b83fbb070b9775/extra_dict/dict.txt.big"
)
DICTIONARY_SIZE = 8_583_143
DICTIONARY_BLOB_SHA1 = "8e3b88ebbc8c42af1f3157f54b7d001c243d672d"
DOWNLOAD_TIMEOUT_SECONDS = 120

# Query limits taken from MaxKB's to_query.
QUERY_MAX_TERMS = 10
QUERY_MAX_KEYWORDS = 20
QUERY_MAX_SINGLE_RUN = 8

# MaxKB drops jieba's English stop words from a query. The list is copied from
# jieba/analyse/tfidf.py (KeywordExtractor.STOP_WORDS), because importing jieba.analyse
# also loads its whole IDF table, which takes about a second.
ENGLISH_STOP_WORDS = frozenset(
    {
        "the", "of", "is", "and", "to", "in", "that", "we", "for", "an", "are",
        "by", "be", "as", "on", "with", "can", "if", "from", "which", "you", "it",
        "this", "then", "at", "have", "all", "not", "one", "has", "or",
    }
)  # fmt: skip


class DictionaryError(LocalSetupError):
    """The Traditional Chinese dictionary could not be downloaded or failed its check."""


@dataclass(frozen=True)
class SearchTokenizer:
    jieba: Any
    user_words: tuple[str, ...]
    # Stored with the search vectors, so a search can tell whether they were built with the same words.
    user_words_digest: str


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _is_expected_dictionary(data: bytes) -> bool:
    return len(data) == DICTIONARY_SIZE and _git_blob_sha1(data) == DICTIONARY_BLOB_SHA1


def ensure_dictionary() -> Path:
    """Return the checked dictionary file, downloading it on first use.

    A failed download raises DictionaryError. There is no fallback to jieba's default
    (Simplified Chinese) dictionary.
    """
    folder = local_data_dir() / "jieba"
    folder.mkdir(exist_ok=True)
    path = folder / "dict.txt.big"
    # The size is checked first, so a wrong file on disk is never read into memory.
    if (
        path.is_file()
        and path.stat().st_size == DICTIONARY_SIZE
        and _is_expected_dictionary(path.read_bytes())
    ):
        return path

    try:
        with urllib.request.urlopen(
            DICTIONARY_URL, timeout=DOWNLOAD_TIMEOUT_SECONDS
        ) as response:
            # One byte past the pinned size is enough to tell that a response is too large,
            # so a replaced source cannot fill memory.
            data: bytes = response.read(DICTIONARY_SIZE + 1)
    except OSError as error:
        raise DictionaryError(
            f"Could not download the Traditional Chinese dictionary from {DICTIONARY_URL}: {error}"
        ) from error
    if len(data) > DICTIONARY_SIZE:
        raise DictionaryError(
            f"The downloaded dictionary is larger than the pinned file ({DICTIONARY_SIZE} bytes)."
        )
    if not _is_expected_dictionary(data):
        raise DictionaryError(
            f"The downloaded dictionary does not match the pinned file "
            f"({len(data)} bytes, expected {DICTIONARY_SIZE})."
        )

    # Write next to the target, then rename, so a crash never leaves a half-written dictionary.
    partial = path.with_name(path.name + ".part")
    partial.write_bytes(data)
    partial.replace(path)
    return path


def _usable_words(user_words: Iterable[str]) -> tuple[str, ...]:
    # jieba cuts text at whitespace before it looks words up, so a user word that contains
    # whitespace could never match and is left out.
    return tuple(
        sorted(
            {word for word in user_words if word and not any(c.isspace() for c in word)}
        )
    )


def user_words_digest(user_words: Iterable[str]) -> str:
    """The digest a tokenizer built from these words would have, without building it."""
    return hashlib.sha256("\n".join(_usable_words(user_words)).encode()).hexdigest()


def build_tokenizer(user_words: Iterable[str]) -> SearchTokenizer:
    """Build a jieba tokenizer on the Traditional Chinese dictionary plus the given user words."""
    jieba.setLogLevel(logging.WARNING)
    dictionary = ensure_dictionary()
    words = _usable_words(user_words)

    tokenizer = jieba.Tokenizer(dictionary=str(dictionary))
    # Keep jieba's prefix-dictionary cache next to the dictionary instead of the system temp folder.
    tokenizer.tmp_dir = str(dictionary.parent)
    for word in words:
        tokenizer.add_word(word)

    return SearchTokenizer(
        jieba=tokenizer, user_words=words, user_words_digest=user_words_digest(words)
    )


def index_text(tokenizer: SearchTokenizer, text: str) -> str:
    """Return the words to index, joined by spaces. Full mode keeps every dictionary word it finds."""
    words: list[str] = tokenizer.jieba.lcut(text, cut_all=True)
    return " ".join(words)


# The CJK Unified Ideographs block, U+4E00 to U+9FFF, the range MaxKB checks.
HAN_FIRST = chr(0x4E00)
HAN_LAST = chr(0x9FFF)


def _is_single_han(token: str) -> bool:
    return len(token) == 1 and HAN_FIRST <= token <= HAN_LAST


def mentions(lowered_text: str, word: str) -> bool:
    """Whether a lowercased text mentions a word.

    MaxKB checks this with a substring test, which is right for Chinese. An English word
    must match as a whole word here, or "AI" would be found inside "raise".
    """
    needle = word.lower()
    if not needle.isascii():
        return needle in lowered_text
    pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
    return re.search(pattern, lowered_text) is not None


def _clean_clause(clause: str) -> str:
    # websearch_to_tsquery reads quotes as phrases and a leading minus as NOT.
    return clause.replace('"', " ").lstrip("-").strip()


def query_clauses(
    tokenizer: SearchTokenizer, text: str, synonyms: Sequence[str] = ()
) -> list[str]:
    """Turn a question into websearch_to_tsquery clauses. An empty list means no word is searchable.

    The steps follow MaxKB's to_query:
    1. User words the question mentions, longest first. English words must match whole words.
    2. Words from jieba's precise mode. A run of single Han characters becomes one clause,
       because the index keeps each of those characters as its own word.
    3. The caller joins the clauses with "or".
    Like MaxKB, jieba's English stop words are dropped. MaxKB also drops words by inverse
    document frequency and by a Chinese stop-word list. Both of those are for Simplified
    Chinese, so that step is not taken here.

    Synonyms of the question's words come last, as RAGFlow gives them a quarter of the
    weight of the question's own words.
    """
    lowered = text.lower()
    terms = [
        word
        for word in sorted(tokenizer.user_words, key=len, reverse=True)
        if mentions(lowered, word)
    ]
    clauses = terms[:QUERY_MAX_TERMS]

    single_run: list[str] = []
    keywords: list[str] = []
    for token in (raw.strip() for raw in tokenizer.jieba.lcut(text, HMM=False)):
        if _is_single_han(token):
            single_run.append(token)
            continue
        if len(single_run) >= 2:
            keywords.append(" ".join(single_run[:QUERY_MAX_SINGLE_RUN]))
        single_run.clear()
        # "or" is in the stop words, so no query word can be read as the OR operator.
        if (
            len(token) < 2
            or token.lower() in ENGLISH_STOP_WORDS
            or not any(c.isalnum() for c in token)
        ):
            continue
        keywords.append(token)
    if len(single_run) >= 2:
        keywords.append(" ".join(single_run[:QUERY_MAX_SINGLE_RUN]))

    seen = {clause.lower() for clause in clauses}
    for keyword in [*keywords[:QUERY_MAX_KEYWORDS], *synonyms]:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            clauses.append(keyword)

    return [clause for clause in (_clean_clause(c) for c in clauses) if clause]
