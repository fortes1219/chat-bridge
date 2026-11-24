"""The chat endpoints."""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Annotated

import anyio
from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette import EventSourceResponse, JSONServerSentEvent

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
# The line separator of the stream. sse-starlette uses \r\n unless told, and each event carries
# its own, so the response and every event are given this one.
SEPARATOR = "\n"
# How long a stream has, once the service begins to shut down, to cut its answer off and say so
# before sse-starlette ends it anyway. Cutting off takes well under a second. It must stay below
# uvicorn's shutdown limit (server.SHUTDOWN_WAIT_SECONDS), or uvicorn ends the stream first.
SHUTDOWN_GRACE_SECONDS = 2
# The message of the last event when the service stops while an answer is being written. The page
# words the code, `answer_failed`, in its own language; this is for logs.
STOPPED_MESSAGE = "the service stopped before the answer ended"

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
) -> EventSourceResponse:
    """Answer a question from the knowledge base, streamed as Server-Sent Events.

    The context comes first, then the answer in pieces, one event each. Once the stream has
    started, the HTTP status can no longer change, so an error becomes a last event named
    `error` that the client can still read.

    When the service begins to shut down (Ctrl+C), sse-starlette sets the stream's shutdown
    event. The answer is then cut off as when the person stops it, and the stream ends with an
    `error` event, so the page does not show part of an answer as the whole; the service stops
    at once. Events are separated by a bare newline, as the page and the tests read them.
    """
    shutdown = anyio.Event()
    return EventSourceResponse(
        _events(request, sections, shutdown),
        sep=SEPARATOR,
        shutdown_event=shutdown,
        shutdown_grace_period=SHUTDOWN_GRACE_SECONDS,
    )


async def _events(
    request: ChatRequest, sections: list[service.FoundSection], shutdown: anyio.Event
) -> AsyncIterator[JSONServerSentEvent]:
    answer = service.answer_stream(request.question, sections, request.program)
    try:
        while True:
            # The wait for each piece is cancelled when the service begins to shut down. It is
            # cancelled in this task, the one writing the answer, so the answer is cut off and
            # recorded as when the person stops it. No piece is sent from inside the scope.
            with anyio.CancelScope() as waiting:
                watcher = asyncio.ensure_future(_cancel_when_set(shutdown, waiting))
                try:
                    delta = await anext(answer, None)
                finally:
                    watcher.cancel()
            if waiting.cancelled_caught:
                yield _error_event("answer_failed", STOPPED_MESSAGE)
                return
            if delta is None:
                return
            # Nulls stay in, so a source without an event date says so instead of losing
            # the field.
            yield JSONServerSentEvent(data=delta.model_dump(mode="json"), sep=SEPARATOR)
    except Exception as error:
        logger.exception("The answer stream stopped")
        # A program that logged out since the page read its state is the one failure a page
        # acts on: it reads the login states again.
        code: ErrorCode = (
            "not_logged_in"
            if isinstance(error, service.NoLoginError)
            else "answer_failed"
        )
        yield _error_event(code, str(error))


async def _cancel_when_set(event: anyio.Event, scope: anyio.CancelScope) -> None:
    await event.wait()
    scope.cancel()


def _error_event(code: ErrorCode, message: str) -> JSONServerSentEvent:
    detail = ErrorDetail(code=code, message=message)
    return JSONServerSentEvent(
        event=ERROR_EVENT, data=detail.model_dump(), sep=SEPARATOR
    )


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
