"""The channels: the sites the person's own agent is sent to for events.

The list is data (`data/channels.json`), with the fields a source list keeps (id, name, url,
enabled, topics, note). The agent is asked once, with web search and web reading, for the events
on the collection targets that the enabled channels reported in the asked dates, each with its
source pages, and is told the events the folder already has. It answers in a JSON shape; a page
off the site of the channel it names is refused, and an event left with no page, or dated outside
the asked dates, is not used.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from chat_bridge.chat import claude_code
from chat_bridge.chat.programs import AnsweringProgram, Program, ProgramError
from chat_bridge.collect.pages import Page
from chat_bridge.collect.store import StoredEvent
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import Rules
from chat_bridge.truth.truth_files import FolderEvent

logger = logging.getLogger(__name__)

CHANNELS_FILE = PROJECT_ROOT / "data" / "channels.json"
PROMPT_FILE = Path(__file__).with_name("channels_prompt.md")
WEB_SCHEMES = ("http", "https")
EVENTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "event_date": {"type": "string"},
                    "about": {"type": "string"},
                    "pages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "channel": {"type": "string"},
                            },
                            "required": ["url", "channel"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["event_date", "about", "pages"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["events"],
    "additionalProperties": False,
}
PROGRAM_NAMES = {Program.CLAUDE_CODE: "Claude Code", Program.CODEX: "Codex"}
# The limit the chat gives one run of a program.
TIME_LIMIT_SECONDS = claude_code.ANSWER_TIMEOUT_SECONDS


class ChannelsFileError(LocalSetupError):
    """The channels file is missing or not the shape. The message says which."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Channel(_Strict):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: str
    enabled: bool
    topics: list[str]
    note: str


class _ChannelsFile(_Strict):
    about: str
    channels: list[_Channel] = Field(min_length=1)

    @model_validator(mode="after")
    def _addresses_and_ids(self) -> Self:
        ids = [channel.id for channel in self.channels]
        if len(set(ids)) != len(ids):
            raise ValueError("a channel id is listed twice")
        for channel in self.channels:
            parts = urlsplit(channel.url)
            if parts.scheme not in WEB_SCHEMES or not parts.hostname:
                raise ValueError(
                    f"channel {channel.id}: not a web address: {channel.url}"
                )
        return self


@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    url: str
    topics: tuple[str, ...]
    note: str

    @property
    def site(self) -> str:
        """The channel's host, the site its pages must be on."""
        return urlsplit(self.url).hostname or ""


@cache
def enabled_channels(path: Path = CHANNELS_FILE) -> tuple[Channel, ...]:
    """The enabled channels, read and checked once. Raises ChannelsFileError."""
    try:
        parsed = _ChannelsFile.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise ChannelsFileError(f"{path.name}: {error}") from error
    return tuple(
        Channel(one.id, one.name, one.url, tuple(one.topics), one.note)
        for one in parsed.channels
        if one.enabled
    )


@cache
def prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def _dates(window: Window) -> str:
    if window.since is None and window.until is None:
        return "Find the latest events."
    since = window.since.isoformat() if window.since else "any date"
    until = window.until.isoformat() if window.until else "today"
    return f"Find the events from {since} to {until}."


def held_events(
    existing: Sequence[FolderEvent], stored: Sequence[StoredEvent]
) -> list[tuple[date, str]]:
    """The events already collected: the truth folder's files and the events stored for `truth`,
    by date."""
    return sorted(
        [(one.event_date, one.title) for one in existing]
        + [(one.event_date, one.about) for one in stored]
    )


def question(
    channels: tuple[Channel, ...],
    rules: Rules,
    window: Window,
    held: Sequence[tuple[date, str]],
) -> str:
    """The agent's input: the dates, the targets, the events already collected, the channels."""
    listed = [
        {
            "id": one.id,
            "name": one.name,
            "url": one.url,
            "topics": list(one.topics),
            "note": one.note,
        }
        for one in channels
    ]
    targets = "\n".join(f"{number}. {text}" for number, text in rules.targets.items())
    have = "\n".join(f"{day.isoformat()}  {title}" for day, title in held) or "(none)"
    return (
        f"{_dates(window)}\n\n<targets>\n{targets}\n</targets>\n\n"
        f"<events_already_collected>\n{have}\n</events_already_collected>\n\n"
        f"<channels>\n{json.dumps(listed, ensure_ascii=False, indent=2)}\n</channels>\n"
    )


class _Page(_Strict):
    url: str
    channel: str


class _Event(_Strict):
    event_date: str
    about: str
    pages: list[_Page]


class _Events(_Strict):
    events: list[_Event]


@dataclass(frozen=True)
class FoundEvent:
    event_date: date
    about: str
    pages: tuple[str, ...]
    # The site of each page's channel, by the page's address.
    sites: dict[str, str]

    def on_their_sites(
        self, read: Sequence[Page]
    ) -> tuple[tuple[Page, ...], tuple[tuple[str, str], ...]]:
        """The pages read whose address after any redirect is still on their channel's site,
        and the others with the reason."""
        kept: list[Page] = []
        moved: list[tuple[str, str]] = []
        for page in read:
            site = self.sites.get(page.asked, "")
            if _on_site((urlsplit(page.url).hostname or "").lower(), site):
                kept.append(page)
            else:
                moved.append(
                    (
                        page.asked,
                        f"it moved to {page.url}, off its channel's site {site}",
                    )
                )
        return tuple(kept), tuple(moved)


@dataclass(frozen=True)
class Found:
    """The events to write, and what was refused (a page or an event) with the reason."""

    events: tuple[FoundEvent, ...]
    refused: tuple[tuple[str, str], ...]


def _on_site(host: str, site: str) -> bool:
    return host == site or host.endswith(f".{site}")


def _event_pages(
    event: _Event, by_id: dict[str, Channel], refused: list[tuple[str, str]]
) -> dict[str, str]:
    """Each page on the site of the channel it names, with that site."""
    pages: dict[str, str] = {}
    for page in event.pages:
        url = page.url.strip()
        host = (urlsplit(url).hostname or "").lower()
        channel = by_id.get(page.channel)
        if channel is None:
            refused.append((url, f"it names no listed channel ({page.channel})"))
        elif not _on_site(host, channel.site):
            refused.append((url, f"it is not on the site of channel {channel.id}"))
        else:
            pages.setdefault(url, channel.site)
    return pages


def read_events(
    reply: dict[str, Any], channels: tuple[Channel, ...], window: Window
) -> Found:
    """The agent's answer, each page checked against the site of the channel it names. Raises
    ValidationError when the answer is not the shape."""
    parsed = _Events.model_validate(reply)
    by_id = {one.id: one for one in channels}
    events: list[FoundEvent] = []
    refused: list[tuple[str, str]] = []
    for event in parsed.events:
        about = event.about.strip()
        try:
            day = date.fromisoformat(event.event_date)
        except ValueError:
            refused.append((about, f"its date is not YYYY-MM-DD: {event.event_date}"))
            continue
        if not window.holds(day):
            refused.append((about, f"its date {day} is outside the asked dates"))
            continue
        pages = _event_pages(event, by_id, refused)
        if not pages:
            refused.append((about, "none of its pages is on a channel's site"))
            continue
        events.append(FoundEvent(day, about, tuple(pages), pages))
    return Found(tuple(events), tuple(refused))


class SearchError(Exception):
    """No channel to ask, or the agent's run failed, ran past its limit, or answered in another
    shape."""


async def search_events(
    channels: Sequence[Channel],
    rules: Rules,
    window: Window,
    held: Sequence[tuple[date, str]],
    program: AnsweringProgram,
    name: str,
    progress: Callable[[str], None],
) -> Found:
    """Ask the person's own program for the channels' events. Raises SearchError."""
    listed = tuple(channels)
    if not listed:
        # Asking about no channel would spend the person's subscription on nothing.
        raise SearchError(f"no channel is enabled in {CHANNELS_FILE.name}")
    progress(
        f"Asking {name} for the events {len(listed)} channels reported. It searches the web "
        f"and can take several minutes (at most {TIME_LIMIT_SECONDS} seconds)."
    )
    try:
        reply = await asyncio.wait_for(
            program.web_reply_in_shape(
                prompt(),
                question(listed, rules, window, held),
                EVENTS_SCHEMA,
                sorted({one.site for one in listed}),
                on_start=lambda args: logger.debug("Started %s", args[0]),
            ),
            TIME_LIMIT_SECONDS,
        )
    except TimeoutError:
        raise SearchError(
            f"{name} did not finish within {TIME_LIMIT_SECONDS} seconds. Ask for fewer days "
            f"with --until, or turn some channels off in {CHANNELS_FILE.name}"
        ) from None
    except ProgramError as error:
        raise SearchError(str(error)) from error
    try:
        return read_events(reply, listed, window)
    except ValidationError:
        raise SearchError(f"{name}'s answer is not in the asked-for shape") from None
