"""What the chat endpoints take and send."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from chat_bridge.chat.programs import DEFAULT_EFFORT, Effort, Login, Program
from chat_bridge.chat.sources import Language as Language
from chat_bridge.chat.sources import Localized as Localized
from chat_bridge.chat.sources import Source as Source
from chat_bridge.strategy.schemas import ProposalEvent

# Far longer than any question; the limit keeps one request from filling the model's input or
# the record table.
MAX_QUESTION_LENGTH = 10_240

DeltaType = Literal[
    "response.context",
    "response.output_text.delta",
    "response.proposal",
    "response.completed",
]


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
    # How hard the program thinks, for every run of the question; only the three levels the page
    # offers are taken.
    effort: Effort = DEFAULT_EFFORT


class ProgramState(BaseModel):
    """One program's login state. The program's own status text stays out: it can name the
    account."""

    program: Program
    state: Login


class SampleQuestions(BaseModel):
    """Questions the page offers before the first one, each in both languages; none when the
    knowledge base does not hold the documents they are about."""

    questions: list[Localized]


class ChatContext(BaseModel):
    """What the program, not the model, says about an answer: its sources and the disclaimer."""

    sources: list[Source]
    # The latest event date in the whole knowledge base: how recent the data is, whatever the
    # search found.
    data_latest_date: date | None
    disclaimer: Localized
    # The program that answers; none when no program is asked, as for a question the data has
    # nothing on, or when none can answer.
    program: Program | None = None
    # The program could not list the question's parts, so only the question as asked was
    # searched. Said, so a failed split never looks like one that worked.
    split_failed: bool = False
    # The question asks to revise the strategy: the answer comes whole, with a proposal event
    # after it, so a page can say what it is waiting for.
    proposal_expected: bool = False


class QuestionUsage(BaseModel):
    """The tokens of every model run of a question, added up. The input counts all of it, the part
    read from the cache included; `unreported_runs` says how many runs reported none and are left
    out, so a partial total never passes for a whole one."""

    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int
    unreported_runs: int


class ChatDelta(BaseModel):
    """One event of the answer's Server-Sent Events stream.

    The first event carries the context, so the sources and the disclaimer arrive even when the
    answer is cut off; each later event carries a piece of the answer. A revision question has one
    more, carrying what came of its proposal. An answer that ended ends with the question's tokens.
    """

    type: DeltaType
    delta: str | None = None
    context: ChatContext | None = None
    proposal: ProposalEvent | None = None
    usage: QuestionUsage | None = None


class ChatRecordPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asked_at: datetime
    question: str
    answer: str
    details: dict[str, Any]
