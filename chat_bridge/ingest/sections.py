"""Turn a file into sections: Markdown at its headings, a PDF by its pages.

The Markdown split follows private-gpt, which builds the document tree at h1 to h6. The
Markdown parser finds the headings, so headings inside code blocks are not mistaken for real
ones.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.front_matter import front_matter_plugin
from pydantic import BaseModel, ConfigDict, Field

from chat_bridge.ingest.readers import (
    RejectReason,
    UnreadableFileError,
    is_paged,
    read_markdown,
    read_pages,
)

HEADING_PATH_SEPARATOR = " > "
# A PDF's text has no headings, so each page is a section under its page label, the place a
# reader looks it up by in the original.
PAGE_HEADING = "Page {label}"

_PARSER = MarkdownIt("commonmark").use(front_matter_plugin)
# CommonMark has no tables; the GFM table rule finds them, so a table is recognized by its
# Markdown structure wherever it comes from, including tables converted from Word or PDF.
_TABLE_PARSER = MarkdownIt("commonmark").enable("table")


class FrontMatter(BaseModel):
    """The front matter fields the knowledge base uses. Other fields are allowed and ignored."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    keyword_groups: list[list[str]] = Field(default_factory=list)
    # The day the event happened. A search given a date leaves out files after it.
    event_date: date | None = None


@dataclass(frozen=True)
class ParsedSection:
    position: int
    heading: str
    content: str


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    keyword_groups: list[list[str]]
    event_date: date | None
    sections: list[ParsedSection]


@dataclass(frozen=True)
class SectionParts:
    """A section's content with its tables taken out, and the tables themselves."""

    text: str
    tables: list[str]


@dataclass(frozen=True)
class _Heading:
    level: int
    title: str
    first_line: int
    end_line: int


def _read_front_matter(tokens: list[Token]) -> tuple[FrontMatter, int]:
    """Return the front matter and the line where the body starts."""
    if not tokens or tokens[0].type != "front_matter":
        return FrontMatter(), 0
    token = tokens[0]
    body_start = token.map[1] if token.map else 0
    try:
        data = yaml.safe_load(token.content)
        return FrontMatter.model_validate(data or {}), body_start
    # A date that does not exist, such as 2026-02-30 without quotes, makes PyYAML raise a
    # plain ValueError, not a YAMLError. pydantic's ValidationError is a ValueError too.
    except (yaml.YAMLError, ValueError) as error:
        raise UnreadableFileError(
            RejectReason.INVALID_FRONT_MATTER, str(error).splitlines()[0]
        ) from error


def _headings(tokens: list[Token]) -> list[_Heading]:
    headings: list[_Heading] = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.map is None:
            continue
        title = tokens[index + 1].content.strip()
        headings.append(_Heading(int(token.tag[1:]), title, token.map[0], token.map[1]))
    return headings


def split_tables(content: str) -> SectionParts:
    """Take the Markdown tables out of a section's content.

    As RAGFlow keeps a table as its own chunk and LlamaIndex parses tables into their own
    elements, a table is searched apart from the text around it.
    """
    lines = content.splitlines()
    table_ranges = [
        (token.map[0], token.map[1])
        for token in _TABLE_PARSER.parse(content)
        if token.type == "table_open" and token.map is not None
    ]
    if not table_ranges:
        return SectionParts(content, [])

    in_table = {line for start, end in table_ranges for line in range(start, end)}
    text = "\n".join(
        line for number, line in enumerate(lines) if number not in in_table
    ).strip()
    tables = ["\n".join(lines[start:end]).strip() for start, end in table_ranges]
    return SectionParts(text, tables)


def read_document(path: Path) -> ParsedDocument:
    """Read a file into sections, or raise UnreadableFileError.

    A PDF's pages are taken as they are, not parsed as Markdown: in plain text, a line such as
    a chart axis's lone "-" would turn the paragraph above it into a heading.
    """
    if not is_paged(path):
        return parse_markdown(read_markdown(path), fallback_title=path.stem)
    sections = [
        ParsedSection(position, PAGE_HEADING.format(label=page.label), page.text)
        for position, page in enumerate(read_pages(path))
    ]
    return ParsedDocument(
        title=path.stem, keyword_groups=[], event_date=None, sections=sections
    )


def parse_markdown(text: str, fallback_title: str) -> ParsedDocument:
    """Split Markdown into sections. Each section keeps the path of headings above it."""
    tokens = _PARSER.parse(text)
    front_matter, body_start = _read_front_matter(tokens)
    headings = _headings(tokens)
    lines = text.splitlines()

    sections: list[ParsedSection] = []
    first_heading_line = headings[0].first_line if headings else len(lines)
    preamble = "\n".join(lines[body_start:first_heading_line]).strip()
    if preamble:
        sections.append(ParsedSection(len(sections), "", preamble))

    # The heading path is kept with an explicit stack: a new heading closes every open heading
    # at its level or deeper.
    open_headings: list[_Heading] = []
    for index, heading in enumerate(headings):
        while open_headings and open_headings[-1].level >= heading.level:
            open_headings.pop()
        open_headings.append(heading)
        next_line = (
            headings[index + 1].first_line if index + 1 < len(headings) else len(lines)
        )
        content = "\n".join(lines[heading.end_line : next_line]).strip()
        if content:
            path = HEADING_PATH_SEPARATOR.join(
                open_heading.title for open_heading in open_headings
            )
            sections.append(ParsedSection(len(sections), path, content))

    title = (
        front_matter.title or (headings[0].title if headings else "") or fallback_title
    )
    return ParsedDocument(
        title=title,
        keyword_groups=front_matter.keyword_groups,
        event_date=front_matter.event_date,
        sections=sections,
    )
