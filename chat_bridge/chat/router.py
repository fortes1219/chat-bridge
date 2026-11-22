"""The chat endpoints."""

import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent

from chat_bridge.chat import service
from chat_bridge.chat.schemas import (
    ChatRecordPublic,
    ChatRequest,
    ProgramState,
)
from chat_bridge.errors import LocalSetupError
from chat_bridge.search.cli import KNOWN_ERRORS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Every list is paged, so one request reads at most this many rows. The range is the one the
# search command allows for --limit.
MIN_LIMIT = 1
MAX_LIMIT = 10_000
DEFAULT_LIMIT = 100


# The event that ends a stream whose answer failed after it started.
ERROR_EVENT = "error"


async def found_sections(request: ChatRequest) -> list[service.FoundSection]:
    """The search, run as a dependency, so it finishes before the stream starts and a search
    that cannot run is an HTTP error, not an event."""
    try:
        return await service.find_sections(request.question)
    except LocalSetupError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except tuple(KNOWN_ERRORS) as error:
        raise HTTPException(
            status_code=503, detail=KNOWN_ERRORS[type(error)]
        ) from error


@router.post("/stream", response_class=EventSourceResponse)
async def chat_stream(
    request: ChatRequest,
    sections: Annotated[list[service.FoundSection], Depends(found_sections)],
) -> AsyncIterator[ServerSentEvent]:
    """Answer a question from the knowledge base, streamed as Server-Sent Events.

    The context comes first, then the answer in pieces, one event each. Once the stream has
    started, the HTTP status can no longer change, so an error becomes a last event named
    `error` that the client can still read.
    """
    try:
        async for delta in service.answer_stream(
            request.question, sections, request.program
        ):
            # Nulls stay in, so a source without an event date says so instead of losing
            # the field.
            yield ServerSentEvent(data=delta.model_dump(mode="json"))
    except Exception as error:
        logger.exception("The answer stream stopped")
        yield ServerSentEvent(event=ERROR_EVENT, data={"message": str(error)})


@router.get("/programs")
async def chat_programs() -> list[ProgramState]:
    """Whether Claude Code and Codex are each installed and logged in, read without starting
    a model."""
    return await service.program_states()


@router.get("/records")
async def chat_records(
    unanswered: bool = False,
    limit: Annotated[int, Query(ge=MIN_LIMIT, le=MAX_LIMIT)] = DEFAULT_LIMIT,
) -> list[ChatRecordPublic]:
    """The newest chat records. With `unanswered=true`, only the questions the search found
    nothing for."""
    return await service.list_records(unanswered=unanswered, limit=limit)
