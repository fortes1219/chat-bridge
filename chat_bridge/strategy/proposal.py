"""The shape a revision answer comes back in, and the checks a proposal must pass to be shown.

What the program hands back is a model's writing, partly from outside text. It is checked here
against the profile and the answer's sources; one that fails is refused with the reason, never
shown and never repaired, so a proposal on the screen is always one the service checked.
"""

from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from chat_bridge.strategy.schemas import ProposalRefusal, Reason, RefusalCode

# A reason is a sentence or two; the bound keeps a pasted document out of the screen and records.
REASON_MAX_CHARS = 1_000
# The shape both programs are asked for. Every field is required and nothing else is allowed, as
# both programs' structured output expects; `proposal` is null when the program proposes nothing.
# The values (known holdings, whole percents from 0 to 100 adding up to 100, known source numbers)
# are checked below on whatever comes back, so they do not depend on how either program reads a
# schema.
PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "proposal": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "targets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "percent": {"type": "integer"},
                                },
                                "required": ["symbol", "percent"],
                                "additionalProperties": False,
                            },
                        },
                        "reasons": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "sources": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                    },
                                },
                                "required": ["text", "sources"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["targets", "reasons"],
                    "additionalProperties": False,
                },
            ]
        },
    },
    "required": ["answer", "proposal"],
    "additionalProperties": False,
}

ReasonText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=REASON_MAX_CHARS),
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TargetReply(_Strict):
    symbol: str
    percent: int


class ReasonReply(_Strict):
    text: ReasonText
    # Every reason cites the sources it rests on (spec User Story 2, scenario 3).
    sources: Annotated[list[int], Field(min_length=1)]


class ProposalReply(_Strict):
    targets: list[TargetReply]
    reasons: Annotated[list[ReasonReply], Field(min_length=1)]


class _AnswerReply(_Strict):
    """The reply's outer shape. The proposal in it is read on its own, so one not in its shape
    costs the proposal, not the answer."""

    answer: str
    proposal: Any


@dataclass(frozen=True)
class RevisionReply:
    answer: str
    # The proposal as read; or why it is not one; or none, when the program proposed nothing.
    proposal: ProposalReply | ProposalRefusal | None


@dataclass(frozen=True)
class CheckedProposal:
    """A proposal that passed every check: a whole percent for every holding and cash."""

    targets: dict[str, int]
    reasons: list[Reason]


def first_problem(error: ValidationError) -> str:
    """The first problem pydantic found, without the input: the input is the model's text."""
    problem = error.errors(include_input=False, include_url=False)[0]
    where = ".".join(str(part) for part in problem["loc"])
    return f"{where}: {problem['msg']}"


def _refusal(code: RefusalCode, message: str) -> ProposalRefusal:
    return ProposalRefusal(code=code, message=message)


def read_reply(reply: dict[str, Any]) -> RevisionReply:
    """The reply as a revision answer. Raises ValidationError when it has no answer to show.

    A proposal not in its shape, such as a reason without a source, is refused with the reason
    and the answer is still shown (spec User Story 2, scenario 4).
    """
    outer = _AnswerReply.model_validate(reply)
    if outer.proposal is None:
        return RevisionReply(answer=outer.answer, proposal=None)
    try:
        proposal = ProposalReply.model_validate(outer.proposal)
    except ValidationError as error:
        refused = _refusal("not_the_shape", first_problem(error))
        return RevisionReply(answer=outer.answer, proposal=refused)
    return RevisionReply(answer=outer.answer, proposal=proposal)


def check_proposal(
    proposal: ProposalReply, symbols: list[str], source_numbers: set[int]
) -> CheckedProposal | ProposalRefusal:
    """The proposal checked against the profile's holdings (cash included) and the numbers of the
    answer's sources, or the first reason it fails.

    Each check returns as soon as it fails, so the reason is the first thing wrong, not a list.
    """
    known = set(symbols)
    targets: dict[str, int] = {}
    for target in proposal.targets:
        if target.symbol not in known:
            return _refusal("unknown_holding", f"{target.symbol} is not in the profile")
        if target.symbol in targets:
            return _refusal("repeated_holding", f"{target.symbol} is listed twice")
        if not 0 <= target.percent <= 100:
            return _refusal(
                "percent_out_of_range",
                f"{target.symbol} is {target.percent}%, outside 0 to 100",
            )
        targets[target.symbol] = target.percent
    missing = [symbol for symbol in symbols if symbol not in targets]
    if missing:
        return _refusal("missing_holding", f"no target for {', '.join(missing)}")
    total = sum(targets.values())
    if total != 100:
        return _refusal("not_100", f"the targets add up to {total}%, not 100%")
    for reason in proposal.reasons:
        unknown = [number for number in reason.sources if number not in source_numbers]
        if unknown:
            return _refusal(
                "unknown_source",
                f"a reason cites source {unknown[0]}, which the answer does not have",
            )
    return CheckedProposal(
        targets={symbol: targets[symbol] for symbol in symbols},
        reasons=[
            Reason(text=reason.text, sources=reason.sources)
            for reason in proposal.reasons
        ],
    )
