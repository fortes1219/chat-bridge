"""The rules a truth file is made by, read from the docs that describe it.

`docs/truth_format.md` gives the collection targets (the numbered list after the paragraph that
names `targets`), the sections (its numbered list of `## …` headings, 「（可省）」 marking one that
may be left out), the front matter keys and the significance values (its table of keys);
`docs/exposure_vocabulary.md` gives the exposure words (each `- `word`：…` line); the markets
come from `data/market_series.json`. Changing them changes what is collected. The front matter
keys are the program's: `ingest` and the market section read them, so a format that lists another
key stops the command.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from chat_bridge.collect.markets import market_series
from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError

FORMAT_FILE = PROJECT_ROOT / "docs" / "truth_format.md"
VOCABULARY_FILE = PROJECT_ROOT / "docs" / "exposure_vocabulary.md"
# The keys the program writes, in the order the sample files have them.
KEYS = (
    "title",
    "event_date",
    "event_time",
    "targets",
    "markets",
    "tickers",
    "exposure",
    "significance",
    "keyword_groups",
    "sources",
)
OPTIONAL_MARK = "（可省）"

_PARSER = MarkdownIt("commonmark").enable("table")
_CODE = re.compile(r"`([^`]+)`")
_HEADING_ITEM = re.compile(r"^`## ([^`]+)`(（可省）)?")
_WORD_ITEM = re.compile(r"^`([^`]+)`：")


class RulesError(LocalSetupError):
    """A doc the rules are read from is missing or gives no rule it should. The message says
    which."""


@dataclass(frozen=True)
class Rules:
    format_text: str
    vocabulary_text: str
    # Each target's number and words.
    targets: dict[int, str]
    # The sections in order, and those that may be left out.
    headings: tuple[str, ...]
    optional: frozenset[str]
    significance: tuple[str, ...]
    exposure: tuple[str, ...]
    markets: tuple[str, ...]


def _inline_after(tokens: list[Token], index: int) -> str:
    """The text of the inline token that follows an opening token."""
    return tokens[index + 1].content if index + 1 < len(tokens) else ""


def _list_items(tokens: list[Token], start: int) -> list[str]:
    """The first-level items of the list that opens at `start`."""
    depth = 0
    items: list[str] = []
    for index in range(start, len(tokens)):
        token = tokens[index]
        if token.type in ("ordered_list_open", "bullet_list_open"):
            depth += 1
        elif token.type in ("ordered_list_close", "bullet_list_close"):
            depth -= 1
            if depth == 0:
                break
        elif token.type == "paragraph_open" and depth == 1:
            items.append(_inline_after(tokens, index))
    return items


def _targets(tokens: list[Token]) -> dict[int, str]:
    """The numbered list after the paragraph that names `targets`."""
    after_paragraph = False
    for index, token in enumerate(tokens):
        if token.type == "paragraph_open" and token.level == 0:
            after_paragraph = "`targets`" in _inline_after(tokens, index)
        elif token.type == "ordered_list_open" and after_paragraph:
            first = int(token.attrGet("start") or 1)
            items = _list_items(tokens, index)
            return {first + number: text for number, text in enumerate(items)}
    return {}


def _headings(tokens: list[Token]) -> tuple[tuple[str, ...], frozenset[str]]:
    """The numbered list whose items are `## …` headings."""
    for index, token in enumerate(tokens):
        if token.type != "ordered_list_open":
            continue
        found = [_HEADING_ITEM.match(item) for item in _list_items(tokens, index)]
        if found and all(found):
            names = tuple(match.group(1) for match in found if match)
            optional = frozenset(
                match.group(1) for match in found if match and match.group(2)
            )
            return names, optional
    return (), frozenset()


def _key_rows(tokens: list[Token]) -> dict[str, str]:
    """The table of keys: each row's key and its second cell."""
    rows: dict[str, str] = {}
    cells: list[str] = []
    in_body = False
    for index, token in enumerate(tokens):
        if token.type == "tbody_open":
            in_body = True
        elif token.type == "tbody_close":
            if rows:
                return rows
            in_body = False
        elif in_body and token.type == "tr_open":
            cells = []
        elif in_body and token.type == "td_open":
            cells.append(_inline_after(tokens, index))
        elif in_body and token.type == "tr_close" and len(cells) >= 2:
            key = _CODE.fullmatch(cells[0].strip())
            if key:
                rows[key.group(1)] = cells[1]
    return rows


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise RulesError(f"{path.name}: {error}") from error


def rules_from(
    format_text: str, vocabulary_text: str, markets: tuple[str, ...]
) -> Rules:
    """The rules in the two docs' texts. Raises RulesError."""
    tokens = _PARSER.parse(format_text)
    targets = _targets(tokens)
    headings, optional = _headings(tokens)
    rows = _key_rows(tokens)
    missing = [
        what
        for what, found in (
            ("the collection targets", targets),
            ("the sections", headings),
            ("the table of keys", rows),
        )
        if not found
    ]
    if missing:
        raise RulesError(f"{FORMAT_FILE.name} gives none of: {', '.join(missing)}")
    if set(rows) != set(KEYS):
        other = sorted(set(rows) ^ set(KEYS))
        raise RulesError(
            f"{FORMAT_FILE.name} lists keys this program does not write, or lacks keys it "
            f"writes: {', '.join(other)}"
        )
    significance = tuple(_CODE.findall(rows["significance"]))
    words = _words(_PARSER.parse(vocabulary_text))
    if not significance or not words or not markets:
        raise RulesError(
            "no significance values, exposure words or markets were found in "
            f"{FORMAT_FILE.name}, {VOCABULARY_FILE.name} and the markets file"
        )
    return Rules(
        format_text,
        vocabulary_text,
        targets,
        headings,
        optional,
        significance,
        words,
        markets,
    )


def _words(tokens: list[Token]) -> tuple[str, ...]:
    """The words of the first bulleted list whose items start with `word`："""
    for index, token in enumerate(tokens):
        if token.type != "bullet_list_open":
            continue
        found = [_WORD_ITEM.match(item) for item in _list_items(tokens, index)]
        if found and all(found):
            return tuple(match.group(1) for match in found if match)
    return ()


@cache
def read_rules() -> Rules:
    """The rules, read once. Raises RulesError, and the markets file's error."""
    markets = tuple(market.code for market in market_series().markets)
    return rules_from(_read(FORMAT_FILE), _read(VOCABULARY_FILE), markets)
