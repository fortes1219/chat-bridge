"""Web pages and feeds, collected into Markdown files that `ingest` reads.

trafilatura downloads and extracts: its downloads stop at its size limit, follow at most its
redirects, and refuse addresses of this machine and its private network; its retry without
certificate checking is turned off. The addresses are asked one at a time, and a site again only
after the wait since its last request, robots.txt included. Each site's robots.txt is read first
and followed, as RFC 9309 asks: a missing one allows everything, one that cannot be read allows
nothing.

What comes back is read as a feed when feedparser reads it as one, as a web page when it is HTML,
and refused otherwise. Each item of a feed is collected as a page; an item whose page cannot be
read is written from the feed's own title, summary and link. Nothing is rewritten by a model.
"""

from __future__ import annotations

import hashlib
import logging
import time as clock
import warnings
from collections.abc import Callable, Iterable
from configparser import ConfigParser
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from time import struct_time
from typing import Literal
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import feedparser
import yaml

from chat_bridge import __version__

with warnings.catch_warnings():
    # trafilatura tries urllib3's SOCKS support at import, which warns when PySocks is not
    # installed; no proxy is used here.
    warnings.simplefilter("ignore")
    import trafilatura
    from trafilatura.downloads import fetch_response
    from trafilatura.settings import DEFAULT_CONFIG, Document
    from trafilatura.utils import Response

USER_AGENT = f"chat-bridge/{__version__}"
# Seconds between two requests to one site: the wait trafilatura's own download loop uses
# (load_download_buffer's sleep_time) and langroid passes to it.
SITE_WAIT_SECONDS = 5.0
# A short hash of the address names the file, so collecting an address again finds its file.
NAME_HASH_LENGTH = 12
HTML_TYPES = ("text/html", "application/xhtml+xml")

logger = logging.getLogger(__name__)


def download_config() -> ConfigParser:
    """trafilatura's settings with its insecure retry turned off and this command's User-Agent;
    its limits on time, size, redirects and private addresses are kept."""
    config = deepcopy(DEFAULT_CONFIG)
    config["DEFAULT"]["INSECURE_SSL_FALLBACK"] = "off"
    config["DEFAULT"]["USER_AGENTS"] = USER_AGENT
    return config


@dataclass(frozen=True)
class Page:
    """A page to write: what the collected file holds."""

    url: str
    title: str
    site: str
    text: str
    published: date | None
    feed: str | None = None
    # Set when the page could not be read and the feed's own summary is written instead.
    from_feed_summary: str | None = None


Kind = Literal["written", "unchanged", "refused"]


@dataclass(frozen=True)
class Outcome:
    url: str
    kind: Kind
    detail: str
    path: Path | None = None

    def line(self) -> str:
        """The outcome as one line of the command's progress."""
        if self.kind == "refused":
            return f"  not collected  {self.url}: {self.detail}"
        name = self.path.name if self.path else ""
        return f"  {self.kind:<9}      {self.url}  ->  {name}"


@dataclass
class _FeedItem:
    feed: str
    title: str
    summary: str
    link: str
    published: date | None


@dataclass
class _Pending:
    url: str
    item: _FeedItem | None = None


Fetch = Callable[[str, ConfigParser], Response | None]


def download(url: str, config: ConfigParser) -> Response | None:
    """One download with trafilatura's limits, decoded; None when it could not be read."""
    return fetch_response(url, decode=True, config=config)


@dataclass
class Pacing:
    """One request at a time, and a site again only `wait` seconds after its last request."""

    wait: float = SITE_WAIT_SECONDS
    now: Callable[[], float] = clock.monotonic
    sleep: Callable[[float], None] = clock.sleep
    last: dict[str, float] = field(default_factory=dict)

    def before(self, url: str) -> None:
        site = _site(url)
        if site in self.last:
            remaining = self.last[site] + self.wait - self.now()
            if remaining > 0:
                self.sleep(remaining)
        self.last[site] = self.now()


def _site(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _robots(text: str | None, status: int | None) -> RobotFileParser:
    """robots.txt as RFC 9309 reads it: a 4xx allows everything, no answer or a 5xx nothing."""
    parser = RobotFileParser()
    if status is not None and 400 <= status < 500:
        parser.parse([])
    elif status is None or status >= 500:
        parser.parse(["User-agent: *", "Disallow: /"])
    else:
        parser.parse((text or "").splitlines())
    return parser


class _Errors(logging.Handler):
    """The last download error trafilatura logs for each address."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())

    def about(self, url: str) -> str:
        return next(
            (message for message in reversed(self.messages) if url in message),
            "it could not be read",
        )


def _date(text: str | None) -> date | None:
    try:
        return None if not text else date.fromisoformat(text[:10])
    except ValueError:
        return None


def _struct_date(value: struct_time | None) -> date | None:
    return None if value is None else date(value.tm_year, value.tm_mon, value.tm_mday)


def _feed_items(url: str, data: bytes) -> list[_FeedItem] | None:
    """The items of a feed, or None when the answer is not a feed."""
    parsed = feedparser.parse(data)
    if not parsed.get("version"):
        return None
    return [
        _FeedItem(
            feed=url,
            title=str(entry.get("title", "")),
            summary=str(entry.get("summary", "")),
            link=str(entry.get("link", "")),
            published=_struct_date(
                entry.get("published_parsed") or entry.get("updated_parsed")
            ),
        )
        for entry in parsed.entries
        if entry.get("link")
    ]


def _page(url: str, html: str, item: _FeedItem | None) -> Page | None:
    text = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_formatting=True,
        include_links=False,
    )
    if not text:
        return None
    found = trafilatura.bare_extraction(html, url=url, with_metadata=True)
    meta = found if isinstance(found, Document) else None
    title = (meta.title if meta else None) or (item.title if item else "") or url
    published = _date(meta.date if meta else None) or (item.published if item else None)
    site = (meta.sitename if meta else None) or urlsplit(url).netloc
    return Page(url, title, site, text, published, item.feed if item else None)


def _summary_page(item: _FeedItem, reason: str) -> Page:
    return Page(
        url=item.link,
        title=item.title or item.link,
        site=urlsplit(item.link).netloc,
        text=item.summary,
        published=item.published,
        feed=item.feed,
        from_feed_summary=reason,
    )


def file_name(url: str) -> str:
    """The file a page is written to: its host and a short hash of its address."""
    parts = urlsplit(url)
    host = parts.hostname or "page"
    if parts.port is not None:
        host = f"{host}_{parts.port}"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:NAME_HASH_LENGTH]
    return f"{host}-{digest}.md"


def _front_matter(page: Page, collected: datetime) -> str:
    fields: dict[str, object] = {
        "title": page.title,
        "url": page.url,
        "site": page.site,
        "collected": collected.isoformat(timespec="seconds"),
    }
    if page.published is not None:
        fields["event_date"] = page.published
    if page.feed is not None:
        fields["feed"] = page.feed
    text: str = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False, width=4096)
    return text


def _body(page: Page) -> str:
    note = (
        f"> This file holds the feed's summary of the item; the page could not be read: "
        f"{page.from_feed_summary}\n\n"
        if page.from_feed_summary
        else ""
    )
    text = page.text.strip()
    # The extracted text often starts with the page's own title as a heading; it is not repeated.
    heading = "" if text.startswith(f"# {page.title}\n") else f"# {page.title}\n\n"
    return f"{heading}{note}{text}\n"


def write_page(page: Page, folder: Path, collected: datetime) -> Outcome:
    """The page's file, written only when its text changed."""
    path = folder / file_name(page.url)
    body = _body(page)
    if path.is_file():
        old = path.read_text(encoding="utf-8")
        if old.split("---\n", 2)[-1].lstrip("\n") == body:
            return Outcome(page.url, "unchanged", "the page has not changed", path)
    folder.mkdir(parents=True, exist_ok=True)
    text = f"---\n{_front_matter(page, collected)}---\n\n{body}"
    path.write_text(text, encoding="utf-8", newline="\n")
    return Outcome(page.url, "written", page.title, path)


@dataclass
class _Run:
    config: ConfigParser
    folder: Path
    now: Callable[[], datetime]
    fetch: Fetch
    pacing: Pacing
    progress: Callable[[str], None]
    robots: dict[str, RobotFileParser] = field(default_factory=dict)
    outcomes: list[Outcome] = field(default_factory=list)
    errors: _Errors = field(default_factory=_Errors)

    def get(self, url: str) -> Response | None:
        self.pacing.before(url)
        return self.fetch(url, self.config)

    def record(self, outcome: Outcome) -> None:
        self.outcomes.append(outcome)
        self.progress(outcome.line())

    def refuse(self, pending: _Pending, reason: str) -> None:
        if pending.item is not None:
            self.record(
                write_page(_summary_page(pending.item, reason), self.folder, self.now())
            )
            return
        self.record(Outcome(pending.url, "refused", reason))

    def allows(self, url: str) -> bool:
        site = _site(url)
        if site not in self.robots:
            response = self.get(f"{site}/robots.txt")
            status = None if response is None else response.status
            self.robots[site] = _robots(
                None if response is None else response.html, status
            )
        return self.robots[site].can_fetch(USER_AGENT, url)

    def collect(self, pending: Iterable[_Pending]) -> list[_Pending]:
        """Download the pending addresses; the items of the feeds among them come back."""
        following: list[_Pending] = []
        for entry in pending:
            parts = urlsplit(entry.url)
            if parts.scheme not in ("http", "https"):
                self.refuse(entry, "it is not an http or https address")
                continue
            if parts.username is not None or parts.password is not None:
                # A user name or password in the address would go into the file and its name.
                self.refuse(
                    entry, "an address with a user name or password is not collected"
                )
                continue
            if not self.allows(entry.url):
                self.refuse(entry, "its site's robots.txt does not allow it")
                continue
            items = self.answer(entry, self.get(entry.url))
            following += [_Pending(item.link, item) for item in items]
        return following

    def answer(self, entry: _Pending, response: Response | None) -> list[_FeedItem]:
        if response is None:
            self.refuse(entry, self.errors.about(entry.url))
            return []
        if response.status != 200:
            self.refuse(entry, f"the site answered with status {response.status}")
            return []
        kind = (response.headers or {}).get("content-type", "").split(";")[0].strip()
        is_html = kind in HTML_TYPES
        if entry.item is None and not is_html:
            items = _feed_items(entry.url, response.data)
            if items is not None:
                if not items:
                    self.refuse(entry, "the feed has no items with a link")
                else:
                    self.progress(f"  feed           {entry.url}: {len(items)} items")
                return items
        if not is_html or not response.html:
            self.refuse(
                entry,
                f"it is not a web page or a feed ({kind or 'no type'}); "
                "download a document such as a PDF and ingest the file",
            )
            return []
        page = _page(response.url or entry.url, response.html, entry.item)
        if page is None:
            self.refuse(entry, "no main text was found in the page")
            return []
        self.record(write_page(page, self.folder, self.now()))
        return []


def collect_addresses(
    urls: list[str],
    folder: Path,
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    fetch: Fetch = download,
    pacing: Pacing | None = None,
    progress: Callable[[str], None] = lambda line: None,
) -> list[Outcome]:
    """Collect each address into `folder`: a page, or each item of a feed. A feed's items come
    after the addresses given, and an item's own link is collected as a page, never as another
    feed, so the loop ends. `progress` is told each outcome as it happens."""
    run = _Run(download_config(), folder, now, fetch, pacing or Pacing(), progress)
    # trafilatura logs why a download failed; the reason goes into the report instead of the
    # terminal, where it would print a second time.
    library = logging.getLogger("trafilatura")
    library.addHandler(run.errors)
    try:
        pending = [_Pending(url) for url in dict.fromkeys(urls)]
        while pending:
            pending = run.collect(pending)
    finally:
        library.removeHandler(run.errors)
    return run.outcomes
