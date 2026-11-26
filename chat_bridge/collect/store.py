"""The events `collect` stores for `truth` to make into files.

Each event is a folder in `local_data/collected/`, named from its date and its pages' addresses, so
the same pages give the same folder and an event is not stored twice. It holds `event.json` (the
event and each page's details) and `s1.txt`, `s2.txt`, … (each page's text as the model is given
it, the same text the passages are looked for in). A folder is written beside its name and renamed
onto it, so it appears whole. `truth` removes an event's folder once the event is a file, or the
truth folder already has it; only a folder under the collected folder, named as this module names
them and holding an `event.json`, is ever removed.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from chat_bridge.collect.pages import Page
from chat_bridge.config import local_data_dir

COLLECTED_NAME = "collected"
EVENT_FILE = "event.json"
# A short hash of the event's page addresses names its folder, after its date.
NAME_HASH_LENGTH = 12
_FOLDER = re.compile(r"^(\d{4}-\d{2}-\d{2})-[0-9a-f]{12}$")
PART_SUFFIX = ".part"


def collected_dir() -> Path:
    return local_data_dir() / COLLECTED_NAME


class StoreError(Exception):
    """A stored event cannot be read, or a folder is not one this module stored. The message
    names the folder."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Page(_Strict):
    id: str
    asked: str
    url: str
    title: str
    site: str
    published: str | None


class _Event(_Strict):
    event_date: str
    about: str
    since: str | None
    until: str | None
    collected: str
    pages: list[_Page]


@dataclass(frozen=True)
class StoredEvent:
    folder: Path
    event_date: date
    about: str
    # The dates the event was asked for.
    since: date | None
    until: date | None

    def read_pages(self) -> tuple[Page, ...]:
        """The event's pages with their text. Raises StoreError."""
        try:
            parsed = _read(self.folder)
            return tuple(
                Page(
                    page.asked,
                    page.url,
                    page.title,
                    page.site,
                    (self.folder / f"{page.id}.txt").read_text(encoding="utf-8"),
                    _day(page.published),
                )
                for page in parsed.pages
            )
        except (OSError, ValueError) as error:
            raise StoreError(f"{self.folder.name}: {error}") from error


def _day(text: str | None) -> date | None:
    return None if text is None else date.fromisoformat(text)


def _read(folder: Path) -> _Event:
    return _Event.model_validate_json((folder / EVENT_FILE).read_text(encoding="utf-8"))


def folder_name(event_date: date, urls: Sequence[str]) -> str:
    digest = hashlib.sha256("\n".join(sorted(urls)).encode("utf-8")).hexdigest()
    return f"{event_date.isoformat()}-{digest[:NAME_HASH_LENGTH]}"


def store(
    root: Path,
    event_date: date,
    about: str,
    since: date | None,
    until: date | None,
    pages: Sequence[Page],
    *,
    now: datetime | None = None,
) -> Path | None:
    """Store the event and its pages' text; None when the same event is stored already."""
    target = root / folder_name(event_date, [page.asked for page in pages])
    if target.exists():
        return None
    root.mkdir(parents=True, exist_ok=True)
    event = _Event(
        event_date=event_date.isoformat(),
        about=about,
        since=since.isoformat() if since else None,
        until=until.isoformat() if until else None,
        collected=(now or datetime.now(UTC)).isoformat(timespec="seconds"),
        pages=[
            _Page(
                id=f"s{number}",
                asked=page.asked,
                url=page.url,
                title=page.title,
                site=page.site,
                published=page.published.isoformat() if page.published else None,
            )
            for number, page in enumerate(pages, 1)
        ],
    )
    part = Path(
        tempfile.mkdtemp(dir=root, prefix=f".{target.name}-", suffix=PART_SUFFIX)
    )
    try:
        for number, page in enumerate(pages, 1):
            (part / f"s{number}.txt").write_text(
                page.text, encoding="utf-8", newline="\n"
            )
        (part / EVENT_FILE).write_text(
            event.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        os.replace(part, target)
    except BaseException:
        shutil.rmtree(part, ignore_errors=True)
        raise
    return target


def stored_events(root: Path, since: date | None = None) -> list[StoredEvent]:
    """The stored events, dated on or after `since` (all with none), by date then name. Raises
    StoreError for an event folder that cannot be read."""
    if not root.is_dir():
        return []
    found: list[StoredEvent] = []
    for folder in sorted(root.iterdir()):
        match = _FOLDER.match(folder.name)
        if not match or not folder.is_dir():
            continue
        if since is not None and date.fromisoformat(match.group(1)) < since:
            continue
        try:
            event = _read(folder)
            found.append(
                StoredEvent(
                    folder,
                    date.fromisoformat(event.event_date),
                    event.about,
                    _day(event.since),
                    _day(event.until),
                )
            )
        except (OSError, ValueError, ValidationError) as error:
            raise StoreError(f"{folder.name}: {error}") from error
    return found


def remove(root: Path, event: StoredEvent) -> None:
    """Remove a stored event's folder, and the collected folder when it is left empty. Raises
    StoreError for a folder that is not a stored event of `root`."""
    folder = event.folder.resolve()
    if (
        folder.parent != root.resolve()
        or not _FOLDER.match(folder.name)
        or not (folder / EVENT_FILE).is_file()
    ):
        raise StoreError(f"{event.folder}: not an event stored in {root}")
    shutil.rmtree(folder)
    if not any(root.iterdir()):
        root.rmdir()
