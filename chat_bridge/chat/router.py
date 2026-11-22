"""The chat endpoints."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from chat_bridge.chat import service
from chat_bridge.chat.schemas import (
    ChatDelta,
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


async def _as_ndjson(deltas: AsyncIterator[ChatDelta]) -> AsyncIterator[str]:
    """One JSON object per line.

    Once the stream has started, the HTTP status can no longer change, so an error becomes a
    last line {"error": ...} that the client can still read.
    """
    try:
        async for delta in deltas:
            # Nulls stay in, so a source without an event date says so instead of losing the field.
            yield delta.model_dump_json() + "\n"
    except Exception as error:
        logger.exception("The answer stream stopped")
        yield json.dumps({"error": str(error)}, ensure_ascii=False) + "\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Answer a question from the knowledge base, streamed as NDJSON.

    The search runs before the stream starts, so a search that cannot run is an HTTP error,
    and the stream itself only waits on the model.
    """
    try:
        sections = await service.find_sections(request.question)
    except LocalSetupError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except tuple(KNOWN_ERRORS) as error:
        raise HTTPException(
            status_code=503, detail=KNOWN_ERRORS[type(error)]
        ) from error
    return StreamingResponse(
        _as_ndjson(service.answer_stream(request.question, sections, request.program)),
        media_type="application/x-ndjson",
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
