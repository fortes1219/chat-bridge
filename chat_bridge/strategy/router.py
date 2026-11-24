"""The strategy endpoints.

The one that changes something takes a JSON body, so FastAPI's strict Content-Type check refuses a
form or a plain-text post, which another web page could send without the browser first asking the
service; and the service adds no CORS rule, so that permission is never given.
"""

from typing import NoReturn

from fastapi import APIRouter, HTTPException

from chat_bridge.strategy import store
from chat_bridge.strategy.schemas import (
    DecisionRequest,
    StrategyErrorDetail,
    StrategyView,
)
from chat_bridge.strategy.state import STATE

router = APIRouter(prefix="/strategy", tags=["strategy"])

# The HTTP status of each refusal.
STATUS_OF: dict[type[store.StrategyError], int] = {
    store.ProfileMissingError: 503,
    store.ProposalNotFoundError: 404,
    store.ProposalNotOpenError: 409,
}


def _refuse(error: store.StrategyError) -> NoReturn:
    detail = StrategyErrorDetail(code=error.code, message=str(error))
    raise HTTPException(
        status_code=STATUS_OF[type(error)], detail=detail.model_dump()
    ) from error


@router.get("")
async def get_strategy() -> StrategyView:
    """The profile, its current targets, the proposal waiting for the person, and the numbers
    that follow the prices."""
    try:
        return await STATE.view()
    except store.StrategyError as error:
        _refuse(error)


@router.post("/proposals/{proposal_id}/decision")
async def decide_proposal(proposal_id: int, request: DecisionRequest) -> StrategyView:
    """Accept or reject the open proposal. Only accepting changes the targets."""
    try:
        STATE.written(await store.decide(proposal_id, request.decision))
        return await STATE.view()
    except store.StrategyError as error:
        _refuse(error)
