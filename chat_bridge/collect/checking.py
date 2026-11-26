"""The second reader: another run of the agent, with no tool and without the writing run, judges
each statement of a record against the passages it rests on, as a faithfulness check judges
statements against a context: a verdict and a reason for each.

The title is judged against every passage of the file, each item against its own passage, and
each note against every passage of the file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from chat_bridge.collect.record import Record

PROMPT_FILE = Path(__file__).with_name("checking_prompt.md")
CHECK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "supported": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["number", "supported", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Statement:
    label: str
    text: str
    passages: tuple[str, ...]


def statements(record: Record) -> tuple[Statement, ...]:
    every = tuple(dict.fromkeys(passage for _, _, passage in record.passages))
    found = [Statement("the title", record.file.title, every)]
    found += [
        Statement(label, item.text, (passage,))
        for label, item, passage in record.passages
    ]
    found += [
        Statement(f"{section.heading} note {number}", note, every)
        for section in record.file.sections
        for number, note in enumerate(section.notes, 1)
    ]
    return tuple(found)


@cache
def prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def question(listed: tuple[Statement, ...]) -> str:
    rows = [
        {"number": number, "statement": one.text, "passages": list(one.passages)}
        for number, one in enumerate(listed, 1)
    ]
    return (
        "Judge each statement against its passages.\n\n<statements>\n"
        + json.dumps(rows, ensure_ascii=False, indent=2)
        + "\n</statements>\n"
    )


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Verdict(_Strict):
    number: int
    supported: bool
    reason: str


class _Verdicts(_Strict):
    verdicts: list[_Verdict]


class CheckError(Exception):
    """The second reader's answer is not one verdict for each statement."""


def rejections(reply: dict[str, Any], listed: tuple[Statement, ...]) -> tuple[str, ...]:
    """The statements the second reader did not find supported, each with its reason. Raises
    CheckError when the answer does not judge each statement once."""
    try:
        verdicts = _Verdicts.model_validate(reply).verdicts
    except ValidationError:
        raise CheckError(
            "the second reader's answer is not in the asked-for shape"
        ) from None
    numbers = sorted(verdict.number for verdict in verdicts)
    if numbers != list(range(1, len(listed) + 1)):
        raise CheckError("the second reader did not judge each statement once")
    return tuple(
        f"{listed[verdict.number - 1].label} is not supported by its passage: "
        f"{verdict.reason}"
        for verdict in sorted(verdicts, key=lambda one: one.number)
        if not verdict.supported
    )
