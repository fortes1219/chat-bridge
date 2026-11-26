"""Web pages and feeds read into plain text, with each page's title, site and date.

trafilatura downloads and extracts: its downloads stop at its size limit, follow at most its
redirects, and refuse addresses of this machine and its private network; its retry without
certificate checking is turned off. The addresses are asked one at a time, and a site again only
after the wait since its last request, robots.txt included. Each site's robots.txt is read first
and followed, as RFC 9309 asks: a missing one allows everything, one that cannot be read allows
nothing.

What comes back is read as a feed when feedparser reads it as one, as a web page when it is HTML,
and refused otherwise. Each item of a feed is read as a page; an item whose page cannot be read is
refused, as every fact of a truth file comes from a page that was opened. Nothing is written here.
"""

from __future__ import annotations

import logging
import time as clock
import warnings
from collections.abc import Callable, Iterable
from configparser import ConfigParser
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import feedparser

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
    """A page that was read: the address asked for, the address it was read at after any
    redirect, and its main text."""

    asked: str
    url: str
    title: str
    site: str
    text: str
    # The date the page shows, or None when it shows none.
    published: date | None


@dataclass(frozen=True)
class Refusal:
    url: str
    reason: str


@dataclass(frozen=True)
class Read:
    pages: tuple[Page, ...]
    refused: tuple[Refusal, ...]


@dataclass
class _FeedItem:
    title: str
    link: str


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


def _feed_items(data: bytes) -> list[_FeedItem] | None:
    """The items of a feed, or None when the answer is not a feed."""
    parsed = feedparser.parse(data)
    if not parsed.get("version"):
        return None
    return [
        _FeedItem(title=str(entry.get("title", "")), link=str(entry.get("link", "")))
        for entry in parsed.entries
        if entry.get("link")
    ]


def _page(asked: str, url: str, html: str, item: _FeedItem | None) -> Page | None:
    # Plain text: the passages an item rests on are looked for in this same text.
    text = trafilatura.extract(html, url=url, include_links=False)
    if not text:
        return None
    found = trafilatura.bare_extraction(html, url=url, with_metadata=True)
    meta = found if isinstance(found, Document) else None
    title = (meta.title if meta else None) or (item.title if item else "") or url
    site = (meta.sitename if meta else None) or urlsplit(url).netloc
    return Page(asked, url, title, site, text, _date(meta.date if meta else None))


@dataclass
class Reader:
    """Reads addresses for one command run: the wait per site and each site's robots.txt hold
    across its calls, so the events of a run share them."""

    fetch: Fetch = download
    pacing: Pacing = field(default_factory=Pacing)
    progress: Callable[[str], None] = lambda line: None
    config: ConfigParser = field(default_factory=download_config)
    robots: dict[str, RobotFileParser] = field(default_factory=dict)
    pages: list[Page] = field(default_factory=list)
    refused: list[Refusal] = field(default_factory=list)
    errors: _Errors = field(default_factory=_Errors)

    def read_addresses(self, urls: Iterable[str]) -> Read:
        """Read each address: a page, or each item of a feed. A feed's items come after the
        addresses given, and an item's own link is read as a page, never as another feed, so
        the loop ends. `progress` is told each page as it is read or refused."""
        self.pages, self.refused = [], []
        # trafilatura logs why a download failed; the reason goes into the report instead of
        # the terminal, where it would print a second time.
        library = logging.getLogger("trafilatura")
        library.addHandler(self.errors)
        try:
            pending = [_Pending(url) for url in dict.fromkeys(urls)]
            while pending:
                pending = self.read(pending)
        finally:
            library.removeHandler(self.errors)
        return Read(tuple(self.pages), tuple(self.refused))

    def get(self, url: str) -> Response | None:
        self.pacing.before(url)
        return self.fetch(url, self.config)

    def refuse(self, url: str, reason: str) -> None:
        self.refused.append(Refusal(url, reason))
        self.progress(f"    not read  {url}: {reason}")

    def allows(self, url: str) -> bool:
        site = _site(url)
        if site not in self.robots:
            response = self.get(f"{site}/robots.txt")
            status = None if response is None else response.status
            self.robots[site] = _robots(
                None if response is None else response.html, status
            )
        return self.robots[site].can_fetch(USER_AGENT, url)

    def read(self, pending: Iterable[_Pending]) -> list[_Pending]:
        """Download the pending addresses; the items of the feeds among them come back."""
        following: list[_Pending] = []
        for entry in pending:
            parts = urlsplit(entry.url)
            if parts.scheme not in ("http", "https"):
                self.refuse(entry.url, "it is not an http or https address")
                continue
            if parts.username is not None or parts.password is not None:
                # A user name or password in the address would go into the file.
                self.refuse(
                    entry.url, "an address with a user name or password is not read"
                )
                continue
            if not self.allows(entry.url):
                self.refuse(entry.url, "its site's robots.txt does not allow it")
                continue
            items = self.answer(entry, self.get(entry.url))
            following += [_Pending(item.link, item) for item in items]
        return following

    def answer(self, entry: _Pending, response: Response | None) -> list[_FeedItem]:
        if response is None:
            self.refuse(entry.url, self.errors.about(entry.url))
            return []
        if response.status != 200:
            self.refuse(entry.url, f"the site answered with status {response.status}")
            return []
        final = response.url or entry.url
        # A redirect to another site is read only when that site's robots.txt allows it too.
        if _site(final) != _site(entry.url) and not self.allows(final):
            self.refuse(
                entry.url, f"it moved to {final}, whose robots.txt does not allow it"
            )
            return []
        kind = (response.headers or {}).get("content-type", "").split(";")[0].strip()
        is_html = kind in HTML_TYPES
        if entry.item is None and not is_html:
            items = _feed_items(response.data)
            if items is not None:
                if not items:
                    self.refuse(entry.url, "the feed has no items with a link")
                else:
                    self.progress(f"    feed      {entry.url}: {len(items)} items")
                return items
        if not is_html or not response.html:
            self.refuse(
                entry.url,
                f"it is not a web page or a feed ({kind or 'no type'}); "
                "download a document such as a PDF and ingest the file",
            )
            return []
        page = _page(entry.url, final, response.html, entry.item)
        if page is None:
            self.refuse(entry.url, "no main text was found in the page")
            return []
        self.pages.append(page)
        self.progress(f"    read      {entry.url}")
        return []
