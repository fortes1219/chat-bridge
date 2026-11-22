"""What the chat endpoints take and send."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from chat_bridge.chat.programs import Login, Program

# Far longer than any question; the limit keeps one request from filling the model's input or
# the record table.
MAX_QUESTION_LENGTH = 10_240

DeltaType = Literal["response.context", "response.output_text.delta"]


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
    heading: str
    event_date: date | None


class ChatContext(BaseModel):
    """What the program, not the model, says about an answer: its sources and the disclaimer."""

    sources: list[Source]
    # The newest event date among the sources: how recent the answer's data is.
    data_latest_date: date | None
    disclaimer: str
    # The program that answers; none when no program is asked, as for a question the data has
    # nothing on, or when none can answer.
    program: Program | None = None


class ChatDelta(BaseModel):
    """One line of the NDJSON stream.

    The first line carries the context, so the sources and the disclaimer arrive even when the
    answer is cut off; each later line carries a piece of the answer.
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
