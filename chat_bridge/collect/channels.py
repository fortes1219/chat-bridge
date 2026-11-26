"""The channels: the sites the person's own agent is sent to for new pages.

The list is data (`data/channels.json`), with the fields a source list keeps (id, name, url,
enabled, topics, note). The agent is asked once for the pages the enabled channels published on
or after a date, and answers in a JSON shape; a page off the channels' sites is refused, and the
rest are collected by the command as any address is.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from chat_bridge.chat import claude_code
from chat_bridge.chat.programs import AnsweringProgram, Program, ProgramError
from chat_bridge.chat.service import PROGRAMS, choose_program
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError
from chat_bridge.search.service import latest_event_date

logger = logging.getLogger(__name__)

CHANNELS_FILE = PROJECT_ROOT / "data" / "channels.json"
PROMPT_FILE = Path(__file__).with_name("channels_prompt.md")
WEB_SCHEMES = ("http", "https")
# The shape the agent answers in: the pages it found, each with its channel. The title and date
# written into a collected file are the page's own, read when it is collected.
FOUND_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
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
        }
    },
    "required": ["pages"],
    "additionalProperties": False,
}


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


def question(channels: tuple[Channel, ...], since: date | None) -> str:
    """The agent's input: the channels as data, and from which date to look."""
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
    when = (
        f"Find the articles published on or after {since.isoformat()}."
        if since is not None
        else "Find the latest articles."
    )
    return f"{when}\n\n<channels>\n{json.dumps(listed, ensure_ascii=False, indent=2)}\n</channels>\n"


class _Page(_Strict):
    url: str
    channel: str


class _Found(_Strict):
    pages: list[_Page]


@dataclass(frozen=True)
class Found:
    """The pages to collect, how many each channel had, and those refused with the reason."""

    pages: tuple[str, ...]
    per_channel: dict[str, int]
    refused: tuple[tuple[str, str], ...]


def _on_site(host: str, site: str) -> bool:
    return host == site or host.endswith(f".{site}")


def read_found(reply: dict[str, Any], channels: tuple[Channel, ...]) -> Found:
    """The agent's answer, each page checked against the site of the channel it names. Raises
    ValidationError when the answer is not the shape."""
    found = _Found.model_validate(reply)
    by_id = {one.id: one for one in channels}
    per_channel = dict.fromkeys(by_id, 0)
    pages: list[str] = []
    refused: list[tuple[str, str]] = []
    for page in found.pages:
        url = page.url.strip()
        host = (urlsplit(url).hostname or "").lower()
        channel = by_id.get(page.channel)
        if channel is None:
            refused.append((url, f"it names no listed channel ({page.channel})"))
        elif not _on_site(host, channel.site):
            refused.append((url, f"it is not on the site of channel {channel.id}"))
        elif url not in pages:
            pages.append(url)
            per_channel[channel.id] += 1
    return Found(tuple(pages), per_channel, tuple(refused))


PROGRAM_NAMES = {Program.CLAUDE_CODE: "Claude Code", Program.CODEX: "Codex"}
# The limit the chat gives one run of a program.
TIME_LIMIT_SECONDS = claude_code.ANSWER_TIMEOUT_SECONDS


class SearchError(Exception):
    """No channel to ask, or the agent's run failed, ran past its limit, or answered in another
    shape."""


@dataclass(frozen=True)
class Search:
    program: Program
    since: date | None
    found: Found


async def search_channels(
    channels: Sequence[Channel],
    progress: Callable[[str], None],
    *,
    programs: Mapping[Program, AnsweringProgram] = PROGRAMS,
    choose: Callable[[None], Awaitable[Program]] = choose_program,
    latest: Callable[[], Awaitable[date | None]] = latest_event_date,
) -> Search:
    """Ask the person's own logged-in program, chosen as the chat chooses it, for the pages the
    channels published on or after the knowledge base's latest event date. Raises the chat's
    NoLoginError when no program is logged in, and SearchError."""
    listed = tuple(channels)
    if not listed:
        # Asking about no channel would spend the person's subscription on nothing.
        raise SearchError(f"no channel is enabled in {CHANNELS_FILE.name}")
    program = await choose(None)
    since = await latest()
    name = PROGRAM_NAMES[program]
    when = f"on or after {since}" if since is not None else "lately"
    progress(
        f"Asking {name} for the pages {len(listed)} channels published {when}. "
        f"It searches the web and can take several minutes (at most {TIME_LIMIT_SECONDS} seconds)."
    )
    try:
        reply = await asyncio.wait_for(
            programs[program].web_reply_in_shape(
                prompt(),
                question(listed, since),
                FOUND_SCHEMA,
                sorted({one.site for one in listed}),
                on_start=lambda args: logger.debug("Started %s", args[0]),
            ),
            TIME_LIMIT_SECONDS,
        )
    except TimeoutError:
        raise SearchError(
            f"{name} did not finish within {TIME_LIMIT_SECONDS} seconds"
        ) from None
    except ProgramError as error:
        raise SearchError(str(error)) from error
    try:
        found = read_found(reply, listed)
    except ValidationError:
        raise SearchError(f"{name}'s answer is not in the asked-for shape") from None
    return Search(program, since, found)
