"""Read the front matter of a Markdown text and split the rest into sections at its headings.

The split follows private-gpt, which builds the document tree at h1 to h6. The Markdown
parser finds the headings, so headings inside code blocks are not mistaken for real ones.
"""

from dataclasses import dataclass

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.front_matter import front_matter_plugin
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chat_bridge.ingest.readers import RejectReason, UnreadableFileError

HEADING_PATH_SEPARATOR = " > "

_PARSER = MarkdownIt("commonmark").use(front_matter_plugin)


class FrontMatter(BaseModel):
    """The front matter fields the knowledge base uses. Other fields are allowed and ignored."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    keyword_groups: list[list[str]] = Field(default_factory=list)


@dataclass(frozen=True)
class ParsedSection:
    position: int
    heading: str
    content: str


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    keyword_groups: list[list[str]]
    sections: list[ParsedSection]


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
    except (yaml.YAMLError, ValidationError) as error:
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
        title=title, keyword_groups=front_matter.keyword_groups, sections=sections
    )
