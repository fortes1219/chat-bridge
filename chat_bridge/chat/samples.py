"""The sample news and the questions about it.

The questions come with the sample news, so they are offered only while it is stored: after a
person replaces the knowledge base with their own documents, questions about the central bank
would point at nothing.
"""

from functools import cache
from pathlib import Path
from typing import Self, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from chat_bridge.chat.sources import Language, Localized
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError
from chat_bridge.ingest import service as ingest_service

# The sample news the service ingests into an empty knowledge base; a fresh clone answers from it
# with no other command.
SAMPLE_NEWS = PROJECT_ROOT / "data" / "truth"
SAMPLE_QUESTIONS_FILE = PROJECT_ROOT / "data" / "sample_questions.json"
LANGUAGES = frozenset(get_args(Language))


class SampleQuestionsFileError(LocalSetupError):
    """The sample questions file is missing or not the shape. The message says which."""


class _SampleQuestionsFile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    about: str
    questions: list[Localized] = Field(min_length=1)

    @model_validator(mode="after")
    def _every_language(self) -> Self:
        for number, question in enumerate(self.questions, start=1):
            if set(question) != LANGUAGES or not all(question.values()):
                raise ValueError(f"question {number} is not in both languages")
        return self


@cache
def sample_questions_file() -> tuple[Localized, ...]:
    """The questions, read and checked once. Raises SampleQuestionsFileError."""
    try:
        text = SAMPLE_QUESTIONS_FILE.read_text(encoding="utf-8")
        return tuple(_SampleQuestionsFile.model_validate_json(text).questions)
    except (OSError, ValidationError) as error:
        raise SampleQuestionsFileError(
            f"{SAMPLE_QUESTIONS_FILE.name}: {error}"
        ) from error


@cache
def sample_news_paths() -> tuple[str, ...]:
    """The paths the sample news is stored under: relative to its folder, as an ingest stores
    them."""
    return tuple(
        sorted(path.relative_to(SAMPLE_NEWS).as_posix() for path in _files(SAMPLE_NEWS))
    )


def _files(folder: Path) -> list[Path]:
    return [path for path in folder.rglob("*") if path.is_file()]


async def sample_questions() -> list[Localized]:
    """The sample questions while any of the sample news is stored; none otherwise."""
    if not await ingest_service.holds_any(sample_news_paths()):
        return []
    return list(sample_questions_file())
