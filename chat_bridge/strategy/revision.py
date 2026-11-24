"""A question that asks to revise the strategy: the answer and a revised strategy, in one shape.

The program gets the sources and, as data, the profile, its targets and its rules. It answers and
proposes in one run, so the proposal's reasons come from the run that wrote the answer; the
answer then arrives whole. The proposal is checked against the profile and the answer's sources
and kept only when it passes.
"""

import asyncio
import functools
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from chat_bridge.chat.programs import AnsweringProgram, Program, ProgramError
from chat_bridge.chat.sources import Source
from chat_bridge.strategy import store
from chat_bridge.strategy.proposal import (
    PROPOSAL_SCHEMA,
    CheckedProposal,
    ProposalReply,
    RevisionReply,
    check_proposal,
    first_problem,
    read_reply,
)
from chat_bridge.strategy.schemas import ProposalEvent, ProposalRefusal

PROMPT_FILE = Path(__file__).with_name("revision_prompt.md")
# The answer's own limit, as for an answer that streams.
ANSWER_TIMEOUT_SECONDS = 600


class RevisionReplyError(ProgramError):
    """The program's reply is not an answer and a proposal in the asked-for shape."""


@functools.cache
def _prompt_template() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def system_prompt(today: date) -> str:
    return _prompt_template().replace("{{CURRENT_DATE}}", today.isoformat())


def strategy_input(profile: store.Profile) -> str:
    """The profile as data between its own tags, so it reads as data, not as part of the rules."""
    data = {
        "holdings": [
            {
                "symbol": holding.symbol,
                "names": holding.names,
                "market": holding.market,
                "currency": holding.currency,
                "quantity": str(holding.quantity),
                "average_cost": str(holding.average_cost),
                "target_percent": profile.targets[holding.symbol],
            }
            for holding in profile.holdings
        ],
        "rules": profile.rules,
    }
    return (
        f"<strategy>\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</strategy>\n"
    )


async def revision_reply(
    program: AnsweringProgram,
    prompt: str,
    input_text: str,
    *,
    on_start: Callable[[list[str]], None],
) -> RevisionReply:
    """Run the program once for the answer and the proposal. Raises ProgramError when the run
    fails, takes too long, or its reply is not that shape."""
    try:
        reply: dict[str, Any] = await asyncio.wait_for(
            program.reply_in_shape(
                prompt, input_text, PROPOSAL_SCHEMA, on_start=on_start
            ),
            ANSWER_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise ProgramError(
            f"the answer did not finish within {ANSWER_TIMEOUT_SECONDS} seconds"
        ) from None
    try:
        return read_reply(reply)
    except ValidationError as error:
        raise RevisionReplyError(
            f"the reply is not an answer and a proposal: {first_problem(error)}"
        ) from None


async def proposal_event(
    proposal: ProposalReply | None,
    profile: store.Profile,
    sources: list[Source],
    *,
    question: str,
    program: Program,
) -> ProposalEvent:
    """The checked proposal, kept as the open one; or why it was refused; or nothing, when the
    program proposed nothing or proposed the targets as they are."""
    if proposal is None:
        return ProposalEvent()
    checked: CheckedProposal | ProposalRefusal = check_proposal(
        proposal, profile.symbols, {source.number for source in sources}
    )
    if isinstance(checked, ProposalRefusal):
        return ProposalEvent(refused=checked)
    # A program that sees no ground for a change may hand back the current targets instead of
    # null. That leaves nothing for the person to decide, so it is not kept and an open proposal
    # stays open.
    if checked.targets == profile.targets:
        return ProposalEvent()
    cited = {number for reason in checked.reasons for number in reason.sources}
    view = await store.save_proposal(
        question,
        program,
        checked,
        [source for source in sources if source.number in cited],
    )
    return ProposalEvent(proposal=view)
