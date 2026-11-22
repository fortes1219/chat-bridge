"""What the chat endpoints take and send."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from chat_bridge.chat.programs import Login, Program

# Far longer than any question; the limit keeps one request from filling the model's input or
# the record table.
MAX_QUESTION_LENGTH = 10_240

DeltaType = Literal["response.context", "response.output_text.delta"]

# The languages the service writes its own texts in. A client shows the one it needs; a reader
# of the API gets both.
Language = Literal["zh-TW", "en"]
# One text in each language, keyed by language, as a localization dictionary in an API.
Localized = dict[Language, str]

# Why a question was refused or its answer failed, for a client to say so in its own language.
# The message beside it is for people reading the API or the logs.
ErrorCode = Literal[
    "knowledge_base_empty",
    "knowledge_base_outdated",
    "setup_failed",
    "not_logged_in",
    "answer_failed",
]


class ErrorDetail(BaseModel):
    """A refusal's `detail`, and the data of a stream's last `error` event."""

    code: ErrorCode
    message: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    # The program that should answer. Without it, the first logged-in one answers.
    program: Program | None = None


class ProgramState(BaseModel):
    """One program's login state. The program's own status text stays out: it can name the
    account."""

    program: Program
    state: Login


class Source(BaseModel):
    """A section the answer may use, numbered as the model sees it."""

    number: int
    file: str
    title: str
    # The document's own words: what the model reads and the records keep.
    heading: str
    # The heading in each language, when it is a section name this app's sample format fixes;
    # null for any other heading, which is shown as the document wrote it.
    heading_localizations: Localized | None = None
    event_date: date | None


class ChatContext(BaseModel):
    """What the program, not the model, says about an answer: its sources and the disclaimer."""

    sources: list[Source]
    # The newest event date among the sources: how recent the answer's data is.
    data_latest_date: date | None
    disclaimer: Localized
    # The program that answers; none when no program is asked, as for a question the data has
    # nothing on, or when none can answer.
    program: Program | None = None


class ChatDelta(BaseModel):
    """One event of the answer's Server-Sent Events stream.

    The first event carries the context, so the sources and the disclaimer arrive even when the
    answer is cut off; each later event carries a piece of the answer.
    """

    type: DeltaType
    delta: str | None = None
    context: ChatContext | None = None


class ChatRecordPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asked_at: datetime
    question: str
    answer: str
    details: dict[str, Any]
