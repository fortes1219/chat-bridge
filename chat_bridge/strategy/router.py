"""The strategy endpoints.

The ones that change something take a JSON body, so FastAPI's strict Content-Type check refuses a
form or a plain-text post, which another web page could send without the browser first asking the
service; and the service adds no CORS rule, so that permission is never given.
"""

from typing import NoReturn

from fastapi import APIRouter, HTTPException

from chat_bridge.strategy import store
from chat_bridge.strategy.schemas import (
    DecisionRequest,
    HoldingsRequest,
    RulesRequest,
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
    store.RuleRefusedError: 422,
    store.HoldingRefusedError: 422,
}


def _refuse(error: store.StrategyError) -> NoReturn:
    detail = StrategyErrorDetail(code=error.code, message=str(error), item=error.item)
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


@router.put("/rules")
async def save_rules(request: RulesRequest) -> StrategyView:
    """Replace the person's rules; the checks come back recomputed on the current targets and on
    the open proposal's."""
    try:
        STATE.written(await store.save_rules(request.rules))
        return await STATE.view()
    except store.StrategyError as error:
        _refuse(error)


@router.put("/holdings")
async def save_holdings(request: HoldingsRequest) -> StrategyView:
    """Replace the person's holdings and cash; the prices then follow the saved holdings, and a
    new holding's price reaches the page over the live connection when it is read."""
    try:
        stored = await store.save_holdings(request)
    except store.StrategyError as error:
        _refuse(error)
    STATE.written(stored)
    STATE.follow(stored.holdings)
    return await STATE.view()
