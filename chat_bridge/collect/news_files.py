"""A news file in the format of `docs/truth_format.md`: what its section of market moves needs,
and the section and its data sources written back.

The front matter is edited in ruamel.yaml's round-trip mode with the indentation the sample files
use, so only the data sources change in it; a round trip of every sample file gives back the same
bytes. The section is found by the Markdown parser's line map of the headings.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from chat_bridge.collect.markets import MarketSeries
from chat_bridge.collect.moves import (
    BACKUP_SOURCE_ID,
    HEADING,
    YAHOO_SOURCE_ID,
    Event,
    Section,
)

# CommonMark has no tables; the GFM table rule finds where the section's table ends.
_PARSER = MarkdownIt("commonmark").use(front_matter_plugin).enable("table")
# The section goes after this one and before the next heading.
AFTER_HEADING = "相關標的"
# A data source's id: "d" and a number, as `docs/truth_format.md` names it.
DATA_SOURCE_PREFIX = "d"
# The last line of a news file, kept after the sections (`docs/truth_format.md` section 2).
CLOSING_LINE = "> significance 依據"


class NewsFileError(Exception):
    """A file that is not a news file the section can be worked out for. The message says why."""


def _yaml() -> YAML:
    yaml = YAML(typ="rt")
    # As the sample files are written: "sources:\n  - id: s1\n    url: …", no wrapping.
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    yaml.preserve_quotes = True
    return yaml


@dataclass
class NewsFile:
    path: Path
    lines: list[str]
    # The front matter's lines, between the two "---" lines.
    front_span: tuple[int, int]
    front: Any
    event: Event


def round_trip(front_text: str) -> str:
    """The front matter as the command writes it back unchanged."""
    yaml = _yaml()
    out = io.StringIO()
    yaml.dump(yaml.load(front_text), out)
    return out.getvalue()


def _moment(value: object, event_date: date) -> datetime | None:
    if value is None:
        return None
    try:
        moment = (
            value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        )
    except ValueError:
        raise NewsFileError(f"event_time is not an ISO 8601 time: {value}") from None
    if moment.tzinfo is None:
        raise NewsFileError(f"event_time has no offset: {value}")
    if moment.date() != event_date:
        raise NewsFileError(
            f"event_time {moment.isoformat()} is on another day than event_date {event_date}"
        )
    return moment


def read(path: Path, listed: MarketSeries) -> NewsFile:
    """The news file at `path`. Raises NewsFileError."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    tokens = _PARSER.parse(text)
    front_token = tokens[0] if tokens and tokens[0].type == "front_matter" else None
    if front_token is None or front_token.map is None:
        raise NewsFileError("no front matter")
    begin, end = front_token.map
    try:
        front = _yaml().load(front_token.content)
    except YAMLError as error:
        raise NewsFileError(f"the front matter is not YAML: {error}") from None
    if not isinstance(front, dict):
        raise NewsFileError("the front matter is not a mapping")
    event_date = front.get("event_date")
    if not isinstance(event_date, date) or isinstance(event_date, datetime):
        raise NewsFileError("no event_date written YYYY-MM-DD")
    markets = front.get("markets")
    if not isinstance(markets, list) or not markets:
        raise NewsFileError("no markets")
    market = listed.market(str(markets[0]))
    if market is None:
        raise NewsFileError(f"market {markets[0]} is not in the markets file")
    event = Event(event_date, market, _moment(front.get("event_time"), event_date))
    # The front matter's own lines: after the opening "---", before the closing one.
    return NewsFile(path, lines, (begin + 1, end - 1), front, event)


@dataclass(frozen=True)
class _Heading:
    name: str
    start: int
    # Where the first table after the heading ends, if one comes before the next heading.
    table_end: int | None


def _headings(text: str) -> list[_Heading]:
    """Each second-level heading, the line it starts on, and the end of its table."""
    tokens = _PARSER.parse(text)
    found: list[_Heading] = []
    for index, token in enumerate(tokens):
        if token.map is None:
            continue
        if token.type == "heading_open" and token.tag == "h2":
            found.append(_Heading(tokens[index + 1].content, token.map[0], None))
        elif token.type == "table_open" and found and found[-1].table_end is None:
            found[-1] = _Heading(found[-1].name, found[-1].start, token.map[1])
    return found


def _section_span(lines: list[str]) -> tuple[int, int]:
    """Where the section goes: the lines it replaces, or an empty span where it is added.

    An existing section ends with its table and the blank line after it; a note written below
    the table belongs to the file and is kept."""
    headings = _headings("\n".join(lines))
    names = [heading.name for heading in headings]
    starts = [heading.start for heading in headings]
    if HEADING in names:
        index = names.index(HEADING)
        end = headings[index].table_end
        if end is None:
            raise NewsFileError(f"the section {HEADING} has no table")
        return starts[index], end + 1 if end < len(lines) and lines[end] == "" else end
    if AFTER_HEADING not in names:
        raise NewsFileError(f"no section {AFTER_HEADING}")
    index = names.index(AFTER_HEADING)
    at = starts[index + 1] if index + 1 < len(starts) else _closing_line(lines)
    return at, at


def _closing_line(lines: list[str]) -> int:
    """The line the sections end on: the closing line when there is one, else the end."""
    for number in range(len(lines) - 1, -1, -1):
        if lines[number].startswith(CLOSING_LINE):
            return number
    return len(lines) - 1 if lines and lines[-1] == "" else len(lines)


def _data_sources(
    section: Section, accessed: datetime, symbols: list[str]
) -> list[Any]:
    """The data source entries the section cites, as YAML the round trip keeps as written."""
    entries = [
        (
            f"- id: {YAHOO_SOURCE_ID}\n"
            "  url: https://query1.finance.yahoo.com/v8/finance/chart/\n"
            f"  publisher: Yahoo Finance chart API（程式下載的日線收盤；{'、'.join(symbols)}）\n"
            "  published: unknown\n"
            f"  accessed: {accessed.isoformat()}\n"
            "  lang: en\n"
            "  format: json\n"
        )
    ]
    if section.uses_backup:
        entries.append(
            f"- id: {BACKUP_SOURCE_ID}\n"
            "  url: https://api.finmindtrade.com/api/v4/data\n"
            "  publisher: FinMind（TaiwanStockPrice 日收盤；程式下載，補 Yahoo 缺的日子）\n"
            "  published: unknown\n"
            f"  accessed: {accessed.isoformat()}\n"
            "  lang: zh-TW\n"
            "  format: json\n"
        )
    loaded: list[Any] = _yaml().load("".join(entries))
    return loaded


def with_section(
    news: NewsFile, section: Section, accessed: datetime, symbols: list[str]
) -> str | None:
    """The file's text with the section and its data sources, or None when the section is the
    same as the file's, so the file is left as it was."""
    begin, end = _section_span(news.lines)
    current = news.lines[begin:end]
    # The lines kept between the table and the next heading: the blank line before it.
    new = [*section.lines, ""]
    if current == new:
        return None
    sources = news.front.get("sources")
    if not isinstance(sources, list):
        raise NewsFileError("no sources list")
    kept = [
        entry
        for entry in sources
        if not str(entry.get("id", "")).startswith(DATA_SOURCE_PREFIX)
    ]
    sources[:] = [*kept, *_data_sources(section, accessed, symbols)]
    out = io.StringIO()
    _yaml().dump(news.front, out)
    front_begin, front_end = news.front_span
    front_lines = out.getvalue().rstrip("\n").split("\n")
    lines = [
        *news.lines[:front_begin],
        *front_lines,
        *news.lines[front_end:begin],
        *new,
        *news.lines[end:],
    ]
    return "\n".join(lines)
