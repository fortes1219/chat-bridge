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
    ErrorCode,
    ErrorDetail,
    ProgramState,
)
from chat_bridge.database import SchemaMismatchError
from chat_bridge.errors import LocalSetupError
from chat_bridge.search.cli import KNOWN_ERRORS
from chat_bridge.search.service import EmptyKnowledgeBaseError, IndexMismatchError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Every list is paged, so one request reads at most this many rows. The range is the one the
# search command allows for --limit.
MIN_LIMIT = 1
MAX_LIMIT = 10_000
DEFAULT_LIMIT = 100


# The event that ends a stream whose answer failed after it started.
ERROR_EVENT = "error"

# Why a search could not run, by the error it raised. Any other local setup error, such as a
# model or a word list that could not be loaded, is `setup_failed`.
SEARCH_ERROR_CODES: dict[type[Exception], ErrorCode] = {
    EmptyKnowledgeBaseError: "knowledge_base_empty",
    IndexMismatchError: "knowledge_base_outdated",
    SchemaMismatchError: "knowledge_base_outdated",
}


def _refusal(code: ErrorCode, message: str) -> HTTPException:
    return HTTPException(
        status_code=503, detail=ErrorDetail(code=code, message=message).model_dump()
    )


async def found_sections(request: ChatRequest) -> list[service.FoundSection]:
    """The search, run as a dependency, so it finishes before the stream starts and a search
    that cannot run is an HTTP error, not an event."""
    try:
        return await service.find_sections(request.question)
    except LocalSetupError as error:
        code = SEARCH_ERROR_CODES.get(type(error), "setup_failed")
        raise _refusal(code, str(error)) from error
    except tuple(KNOWN_ERRORS) as error:
        raise _refusal(
            SEARCH_ERROR_CODES[type(error)], KNOWN_ERRORS[type(error)]
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
        # A program that logged out since the page read its state is the one failure a page
        # acts on: it reads the login states again.
        code: ErrorCode = (
            "not_logged_in"
            if isinstance(error, service.NoLoginError)
            else "answer_failed"
        )
        detail = ErrorDetail(code=code, message=str(error))
        yield ServerSentEvent(event=ERROR_EVENT, data=detail.model_dump())


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
