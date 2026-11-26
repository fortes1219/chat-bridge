"""Pages given as web addresses, sorted into events by the agent with no tool.

The agent gets each page's text as data, numbered p1, p2, …, with the collection targets, and
answers with the events those pages report and the pages that bear on no target, in a JSON shape.
A page id it did not get, or an event dated outside the asked dates, is not used.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from chat_bridge.collect.pages import Page
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import Rules

PROMPT_FILE = Path(__file__).with_name("grouping_prompt.md")


def groups_schema(ids: list[str]) -> dict[str, Any]:
    page_id = {"type": "string", "enum": ids}
    return {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event_date": {"type": "string"},
                        "about": {"type": "string"},
                        "pages": {"type": "array", "items": page_id},
                    },
                    "required": ["event_date", "about", "pages"],
                    "additionalProperties": False,
                },
            },
            "not_events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"page": page_id, "reason": {"type": "string"}},
                    "required": ["page", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["events", "not_events"],
        "additionalProperties": False,
    }


@cache
def prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def numbered(pages: tuple[Page, ...]) -> dict[str, Page]:
    return {f"p{number}": page for number, page in enumerate(pages, 1)}


def question(pages: dict[str, Page], rules: Rules, window: Window) -> str:
    targets = "\n".join(f"{number}. {text}" for number, text in rules.targets.items())
    since = window.since.isoformat() if window.since else "any date"
    until = window.until.isoformat() if window.until else "today"
    parts = [
        f"Sort these pages into events from {since} to {until}.",
        f"<targets>\n{targets}\n</targets>",
    ]
    for page_id, page in pages.items():
        published = page.published.isoformat() if page.published else "unknown"
        parts.append(
            f'<page id="{page_id}" url="{page.url}" site="{page.site}" '
            f'published="{published}" title={json.dumps(page.title, ensure_ascii=False)}>\n'
            f"{page.text}\n</page>"
        )
    return "\n\n".join(parts) + "\n"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Event(_Strict):
    event_date: str
    about: str
    pages: list[str]


class _NotEvent(_Strict):
    page: str
    reason: str


class _Groups(_Strict):
    events: list[_Event]
    not_events: list[_NotEvent]


@dataclass(frozen=True)
class Group:
    event_date: date
    about: str
    pages: tuple[Page, ...]


@dataclass(frozen=True)
class Groups:
    events: tuple[Group, ...]
    # What was not used (an event or a page), with the reason.
    refused: tuple[tuple[str, str], ...]


class GroupingError(Exception):
    """The agent's answer is not in the asked-for shape."""


def read_groups(
    reply: dict[str, Any], pages: dict[str, Page], window: Window
) -> Groups:
    """The events, each with its pages; pages in no event are named. Raises GroupingError."""
    try:
        parsed = _Groups.model_validate(reply)
    except ValidationError:
        raise GroupingError("the answer is not in the asked-for shape") from None
    events: list[Group] = []
    refused: list[tuple[str, str]] = []
    used: set[str] = set()
    for event in parsed.events:
        about = event.about.strip()
        ids = [one for one in dict.fromkeys(event.pages) if one in pages]
        try:
            day = date.fromisoformat(event.event_date)
        except ValueError:
            refused.append((about, f"its date is not YYYY-MM-DD: {event.event_date}"))
            continue
        if not window.holds(day):
            refused.append((about, f"its date {day} is outside the asked dates"))
            continue
        if not ids:
            refused.append((about, "it names none of the pages given"))
            continue
        used.update(ids)
        events.append(Group(day, about, tuple(pages[one] for one in ids)))
    reasons = {one.page: one.reason for one in parsed.not_events}
    for page_id, page in pages.items():
        if page_id not in used:
            reason = reasons.get(page_id, "the agent put it in no event")
            refused.append((page.url, f"bears on no collection target: {reason}"))
    return Groups(tuple(events), tuple(refused))
