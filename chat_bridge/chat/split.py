"""Lists the separate things a question asks about, so each can be searched on its own.

One search ranks a question's parts against each other, and a part that ranks low is crowded out
of the sections the model is given. So the program that will answer is first asked, once and with
all tools off, for the question's parts as JSON; each part is then searched on its own.

What comes back is a model's writing from outside text. It is checked here and used only as search
text. A split that fails is reported, never passed off as a working one: the answer then goes on
with the question's own sections and says so.
"""

import asyncio
import functools
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from chat_bridge.chat.programs import AnsweringProgram, Effort, ProgramError, Usage

# A safety bound, not a value tuned on test questions: it keeps a question, or text pasted into
# one, from making one answer run dozens of searches. Long questions are split into about eight
# parts. A model may list more than it is asked for, so parts past the bound are left out.
PARTS_LIMIT = 8
# Longer than any part of a real question measured (55 characters; a whole sentence 129), and far
# shorter than a pasted document.
PART_MAX_CHARS = 200
# Well past the 8 to 19 seconds a program takes to start and write, and well short of the answer's
# own limit, so a stuck split costs the person a fraction of the answer's wait.
SPLIT_TIMEOUT_SECONDS = 120
# Longer than any symbol or YYYY-MM-DD date; what is in them is checked with the lookups.
PRICE_FIELD_MAX_CHARS = 32
PROMPT_FILE = Path(__file__).with_name("split_prompt.md")
# The shape both programs are asked for: the parts, whether the question asks to change the
# person's strategy, and the prices to look up, nothing else. The count and the lengths are
# checked below, on whatever comes back, so they do not depend on how either program reads a
# schema; what the lookups name is checked when they are run.
SPLIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "parts": {"type": "array", "items": {"type": "string"}},
        "revise_strategy": {"type": "boolean"},
        "prices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["symbol", "start_date", "end_date"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["parts", "revise_strategy", "prices"],
    "additionalProperties": False,
}

Part = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=PART_MAX_CHARS),
]
PriceField = Annotated[str, StringConstraints(max_length=PRICE_FIELD_MAX_CHARS)]


class PriceRequest(BaseModel):
    """A lookup as the split names it: a symbol and a period."""

    model_config = ConfigDict(extra="forbid", strict=True)

    symbol: PriceField
    start_date: PriceField
    end_date: PriceField


class SplitReply(BaseModel):
    """What a split must return: the parts, whether the question asks for a revision, and the
    prices to look up."""

    model_config = ConfigDict(extra="forbid", strict=True)

    parts: list[Part]
    revise_strategy: bool
    # A reply without it looks nothing up rather than losing its parts.
    prices: list[PriceRequest] = Field(default_factory=list)


@dataclass(frozen=True)
class SplitOutcome:
    """What the split gave: the parts kept, or why it failed."""

    parts: list[str] = field(default_factory=list)
    # Distinct parts past PARTS_LIMIT, left out.
    left_out: int = 0
    # Why the split failed; None when it worked, including when the question had one part.
    error: str | None = None
    # The question asks to change the person's strategy, so the answer comes with a proposal.
    # False when the split failed: no proposal is asked for then.
    revise: bool = False
    # The prices the split asks to look up, as it named them; checked before they are read.
    prices: list[PriceRequest] = field(default_factory=list)
    seconds: float = 0.0
    command_line: list[str] = field(default_factory=list)
    # The tokens the split's run reported; None when it reported none, as a run stopped at the
    # time limit.
    usage: Usage | None = None

    @property
    def failed(self) -> bool:
        return self.error is not None


@functools.cache
def _prompt_template() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def split_prompt(today: date) -> str:
    # Today's date lets the program name the period of "the last two months".
    return _prompt_template().replace("{{CURRENT_DATE}}", today.isoformat())


def _tagged(tag: str, lines: list[str] | None) -> str:
    return f"<{tag}>\n{chr(10).join(lines)}\n</{tag}>\n\n" if lines else ""


def split_input(
    question: str, holdings: list[str] | None = None, series: list[str] | None = None
) -> str:
    """The question between tags, so it reads as data, not as part of the rules; before it, the
    user's own holdings and the listed series, one per line, so a question about them can be
    searched for each one and their prices looked up."""
    return (
        f"{_tagged('holdings', holdings)}{_tagged('series', series)}"
        f"<question>\n{question}\n</question>\n"
    )


def read_split(reply: dict[str, Any]) -> SplitReply:
    """Raises ValidationError when the reply is not a list of parts of allowed length and the
    revision flag."""
    return SplitReply.model_validate(reply)


def kept_parts(question: str, parts: list[str]) -> tuple[list[str], int]:
    """The distinct parts to search, at most PARTS_LIMIT, and how many were left out.

    A part that is the question itself, or repeats an earlier one, would search the same text
    twice.
    """
    seen = {question.strip()}
    distinct: list[str] = []
    for part in parts:
        if part in seen:
            continue
        seen.add(part)
        distinct.append(part)
    return distinct[:PARTS_LIMIT], max(len(distinct) - PARTS_LIMIT, 0)


async def split_question(
    program: AnsweringProgram,
    question: str,
    holdings: list[str] | None = None,
    *,
    series: list[str] | None = None,
    today: date | None = None,
    effort: Effort | None = None,
) -> SplitOutcome:
    """Ask the program for the question's parts and the prices to look up, given the user's
    holdings and the listed series, at the question's level. Never raises for a split that
    fails: the outcome says why, and the caller goes on with the question's own sections."""
    command: list[str] = []
    reported: list[Usage] = []
    started = time.perf_counter()

    def outcome(**fields: Any) -> SplitOutcome:
        return SplitOutcome(
            seconds=round(time.perf_counter() - started, 3),
            command_line=command,
            usage=reported[-1] if reported else None,
            **fields,
        )

    try:
        reply = await asyncio.wait_for(
            program.reply_in_shape(
                split_prompt(today or date.today()),
                split_input(question, holdings, series),
                SPLIT_SCHEMA,
                on_start=command.extend,
                effort=effort,
                on_usage=reported.append,
            ),
            SPLIT_TIMEOUT_SECONDS,
        )
        split = read_split(reply)
        parts, left_out = kept_parts(question, split.parts)
    except TimeoutError:
        return outcome(
            error=f"the split did not finish within {SPLIT_TIMEOUT_SECONDS} seconds"
        )
    except ValidationError as error:
        return outcome(
            error=f"the split's reply is not the asked-for shape: {_first_problem(error)}"
        )
    except (ProgramError, OSError) as error:
        return outcome(error=str(error) or type(error).__name__)
    return outcome(
        parts=parts,
        left_out=left_out,
        revise=split.revise_strategy,
        prices=split.prices,
    )


def _first_problem(error: ValidationError) -> str:
    """The first problem pydantic found, without the input: the input is the model's text."""
    problem = error.errors(include_input=False, include_url=False)[0]
    where = ".".join(str(part) for part in problem["loc"])
    return f"{where}: {problem['msg']}"
