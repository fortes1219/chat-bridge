"""An event written by the agent as a record, and the program's checks of it.

The agent gets the event's pages as numbered sources (`s1`, `s2`, …) and answers in a JSON schema
built from the rules: the targets, markets, exposure words, significance values, headings and
source ids are enums. Each item carries the id of its source and the passage of that source it
rests on. The program checks the record again, and checks what a schema cannot: each passage is
in its page (white space aside), each item is in its source's language, no quantity is left
written with 萬, 億, 兆 or 碼 after a numeral, each conversion's original is in its page and its
result in the file, the date is in the asked window.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from chat_bridge.collect.news_files import NewsFileError, event_moment
from chat_bridge.collect.pages import Page
from chat_bridge.truth.rules import Rules
from chat_bridge.truth.truth_files import (
    Conversion,
    FolderEvent,
    Item,
    Section,
    SourceEntry,
    TruthFile,
)

PROMPT_FILE = Path(__file__).with_name("writing_prompt.md")
# 萬, 億, 兆 or 碼 right after a numeral (format section 3); a name such as 兆豐金 or a phrase
# such as 萬一 has no numeral before it.
_UNCONVERTED = re.compile(r"[0-9０-９〇零一二兩三四五六七八九十百千半]\s?[萬億兆碼]")
_HAN = re.compile(r"[㐀-䶿一-鿿]")
_CITATION = re.compile(r"\[s\d+\]")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_LANG = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


@dataclass(frozen=True)
class Source:
    id: str
    page: Page


@dataclass(frozen=True)
class Window:
    since: date | None
    until: date | None

    def holds(self, day: date) -> bool:
        return (self.since is None or day >= self.since) and (
            self.until is None or day <= self.until
        )


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Item(_Strict):
    text: str
    source: str
    passage: str


class _Section(_Strict):
    heading: str
    items: list[_Item]
    notes: list[str]


class _SourceFields(_Strict):
    id: str
    publisher: str
    lang: str


class _Conversion(_Strict):
    source: str
    original: str
    converted: str
    note: str


class RecordReply(_Strict):
    same_as: str | None
    title: str
    slug: str
    event_date: str
    event_time: str | None
    targets: list[int]
    markets: list[str]
    tickers: list[str]
    exposure: list[str]
    significance: str
    significance_reason: str
    keyword_groups: list[list[str]]
    sources: list[_SourceFields]
    sections: list[_Section]
    conversions: list[_Conversion]


def _string() -> dict[str, Any]:
    return {"type": "string"}


def _array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    # Every key required and no other: the strict shape both programs accept.
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _enum(values: list[Any], kind: str = "string") -> dict[str, Any]:
    return {"type": kind, "enum": values}


def record_schema(rules: Rules, ids: list[str], held: list[str]) -> dict[str, Any]:
    """The record's JSON schema, its fixed values taken from the rules; `same_as` is one of the
    folder's files of the event's date, or null."""
    source_id = _enum(ids)
    item = _object({"text": _string(), "source": source_id, "passage": _string()})
    return _object(
        {
            # A nullable enum, written as Codex's issue labeler writes its product.
            "same_as": {"type": ["string", "null"], "enum": [*held, None]},
            "title": _string(),
            "slug": _string(),
            "event_date": _string(),
            "event_time": {"type": ["string", "null"]},
            "targets": _array(_enum(sorted(rules.targets), "integer")),
            "markets": _array(_enum(list(rules.markets))),
            "tickers": _array(_string()),
            "exposure": _array(_enum(list(rules.exposure))),
            "significance": _enum(list(rules.significance)),
            "significance_reason": _string(),
            "keyword_groups": _array(_array(_string())),
            "sources": _array(
                _object({"id": source_id, "publisher": _string(), "lang": _string()})
            ),
            "sections": _array(
                _object(
                    {
                        "heading": _enum(list(rules.headings)),
                        "items": _array(item),
                        "notes": _array(_string()),
                    }
                )
            ),
            "conversions": _array(
                _object(
                    {
                        "source": source_id,
                        "original": _string(),
                        "converted": _string(),
                        "note": _string(),
                    }
                )
            ),
        }
    )


@cache
def _prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def system_prompt(rules: Rules, example: str | None) -> str:
    """The agent's instructions, the two docs as its rules, and one file as an example."""
    parts = [
        _prompt(),
        f"<format>\n{rules.format_text}\n</format>",
        f"<vocabulary>\n{rules.vocabulary_text}\n</vocabulary>",
    ]
    if example is not None:
        parts.append(f"<example>\n{example}\n</example>")
    return "\n\n".join(parts) + "\n"


@dataclass(frozen=True)
class Again:
    """A record that was refused, and why: given back to the agent once."""

    reply: dict[str, Any]
    reasons: tuple[str, ...]


def question(
    about: str,
    sources: tuple[Source, ...],
    window: Window,
    held: Sequence[FolderEvent],
    again: Again | None,
) -> str:
    """The agent's input: the event, the asked dates, the folder's files of the event's date,
    the sources' text as data."""
    since = window.since.isoformat() if window.since else "any date"
    until = window.until.isoformat() if window.until else "today"
    listed = "\n".join(f"{one.path.name}  {one.title}" for one in held) or "(none)"
    parts = [
        f"Write this event as one record: {about}",
        f"The event's date must be from {since} to {until}.",
        "The folder already has these files of the event's date. If this event is one of "
        "them, give its file name in same_as; otherwise same_as is null.\n"
        f"<events_already_collected>\n{listed}\n</events_already_collected>",
    ]
    for source in sources:
        page = source.page
        published = page.published.isoformat() if page.published else "unknown"
        parts.append(
            f'<source id="{source.id}" url="{page.url}" site="{page.site}" '
            f'published="{published}">\n{page.text}\n</source>'
        )
    if again is not None:
        parts.append(
            "Your earlier record was refused for these reasons; write the record again so "
            "that none of them holds:\n"
            + "\n".join(f"- {reason}" for reason in again.reasons)
            + f"\n<earlier_record>\n{json.dumps(again.reply, ensure_ascii=False)}\n"
            "</earlier_record>"
        )
    return "\n\n".join(parts) + "\n"


def flat(text: str) -> str:
    """Runs of white space made one space: how a passage is looked for in its page."""
    return " ".join(text.split())


def same_as(reply: dict[str, Any], held: Sequence[FolderEvent]) -> FolderEvent | None:
    """The folder's file the agent says this event already is, when it names one of them."""
    name = reply.get("same_as")
    return next((one for one in held if one.path.name == name), None)


@dataclass(frozen=True)
class Record:
    """A record that passed the program's checks, with each item's passage for the second
    reader."""

    file: TruthFile
    slug: str
    passages: tuple[tuple[str, Item, str], ...]
    conversions: tuple[Conversion, ...]


def _language_fits(text: str, lang: str) -> bool:
    has_han = _HAN.search(text) is not None
    return has_han if lang.lower().startswith("zh") else not has_han


class _Checker:
    def __init__(
        self, reply: RecordReply, sources: tuple[Source, ...], rules: Rules
    ) -> None:
        self.reply = reply
        self.rules = rules
        self.pages = {source.id: flat(source.page.text) for source in sources}
        self.langs = {entry.id: entry.lang for entry in reply.sources}
        self.reasons: list[str] = []

    def no(self, reason: str) -> None:
        self.reasons.append(reason)

    def lists(self) -> None:
        reply, rules = self.reply, self.rules
        if not reply.targets or any(one not in rules.targets for one in reply.targets):
            self.no(f"targets must be one or more of {sorted(rules.targets)}")
        if not reply.markets or any(one not in rules.markets for one in reply.markets):
            self.no(f"markets must be one or more of {list(rules.markets)}")
        unknown = [word for word in reply.exposure if word not in rules.exposure]
        if unknown:
            self.no(f"exposure words not in the vocabulary: {', '.join(unknown)}")
        if reply.significance not in rules.significance:
            self.no(f"significance must be one of {list(rules.significance)}")
        if not reply.significance_reason.strip():
            self.no("the significance has no reason")
        if not _SLUG.fullmatch(reply.slug):
            self.no("the slug must be lowercase English words joined by hyphens")
        if any(
            not group or not all(name.strip() for name in group)
            for group in reply.keyword_groups
        ):
            self.no("a keyword group is empty or has an empty name")

    def sources(self) -> None:
        ids = [entry.id for entry in self.reply.sources]
        if len(set(ids)) != len(ids):
            self.no("a source is listed twice in sources")
        for entry in self.reply.sources:
            if entry.id not in self.pages:
                self.no(f"sources lists {entry.id}, which was not given")
            if not entry.publisher.strip():
                self.no(f"{entry.id} has no publisher")
            if not _LANG.fullmatch(entry.lang):
                self.no(f"{entry.id}'s lang is not a language tag such as en or zh-TW")

    def title(self) -> None:
        if not self.reply.title.strip():
            self.no("the title is empty")
        if _UNCONVERTED.search(self.reply.title):
            self.no("the title still writes a quantity with 萬, 億, 兆 or 碼")

    def item(self, label: str, item: _Item) -> None:
        if item.source not in self.pages:
            self.no(f"{label} cites {item.source}, which was not given")
            return
        if item.source not in self.langs:
            self.no(f"{label} cites {item.source}, which sources does not list")
        if not item.text.strip():
            self.no(f"{label} is empty")
        if _CITATION.search(item.text):
            self.no(f"{label} writes its [sN]; the program adds it")
        if (
            not item.passage.strip()
            or flat(item.passage) not in self.pages[item.source]
        ):
            self.no(f"{label}: its passage is not in the text of {item.source}")
        lang = self.langs.get(item.source, "")
        if lang and not _language_fits(item.text, lang):
            self.no(f"{label} is not in the language of {item.source} ({lang})")
        if _UNCONVERTED.search(item.text):
            self.no(f"{label} still writes a quantity with 萬, 億, 兆 or 碼")

    def sections(self) -> list[tuple[str, _Item]]:
        headings = [section.heading for section in self.reply.sections]
        order = [heading for heading in self.rules.headings if heading in headings]
        if headings != order:
            self.no(
                "the sections must each come once, in this order: "
                + ", ".join(self.rules.headings)
            )
        required = [
            one for one in self.rules.headings if one not in self.rules.optional
        ]
        for heading in required:
            if heading not in headings:
                self.no(f"the section {heading} is missing")
        labelled: list[tuple[str, _Item]] = []
        for section in self.reply.sections:
            if section.heading in required and not section.items and not section.notes:
                self.no(f"the section {section.heading} has no item and no note")
            labelled += [
                (f"{section.heading} item {number}", item)
                for number, item in enumerate(section.items, 1)
            ]
        if not labelled:
            self.no("the record has no item")
        return labelled

    def conversions(self, written: str) -> None:
        for number, one in enumerate(self.reply.conversions, 1):
            label = f"conversion {number} ({one.original})"
            if one.source not in self.pages:
                self.no(f"{label} cites {one.source}, which was not given")
            elif flat(one.original) not in self.pages[one.source]:
                self.no(f"{label}: its original is not in the text of {one.source}")
            if flat(one.converted) not in written:
                self.no(f"{label}: its result is not in the title or an item")


def _event_date(reply: RecordReply, window: Window) -> tuple[date | None, list[str]]:
    try:
        day = date.fromisoformat(reply.event_date)
    except ValueError:
        return None, [
            f"event_date is not a date written YYYY-MM-DD: {reply.event_date}"
        ]
    reasons = (
        [] if window.holds(day) else [f"event_date {day} is outside the asked dates"]
    )
    try:
        event_moment(reply.event_time, day)
    except NewsFileError as error:
        reasons.append(str(error))
    return day, reasons


def check_record(
    reply: dict[str, Any],
    sources: tuple[Source, ...],
    rules: Rules,
    window: Window,
    accessed: date,
) -> tuple[Record | None, tuple[str, ...]]:
    """The record and no reasons when it passes; None and every reason it fails."""
    try:
        parsed = RecordReply.model_validate(reply)
    except ValidationError as error:
        return None, (f"the record is not in the asked-for shape: {error}",)
    checker = _Checker(parsed, sources, rules)
    if parsed.same_as is not None:
        # One of the folder's files is taken before the checks (`same_as`); any other is not.
        checker.no(f"same_as names no file of the folder: {parsed.same_as}")
    day, date_reasons = _event_date(parsed, window)
    checker.reasons += date_reasons
    checker.lists()
    checker.sources()
    checker.title()
    labelled = checker.sections()
    for label, item in labelled:
        checker.item(label, item)
    written = flat(" ".join([parsed.title, *(item.text for _, item in labelled)]))
    checker.conversions(written)
    if checker.reasons or day is None:
        return None, tuple(checker.reasons)
    return _record(parsed, sources, day, accessed, labelled), ()


def _record(
    reply: RecordReply,
    sources: tuple[Source, ...],
    day: date,
    accessed: date,
    labelled: list[tuple[str, _Item]],
) -> Record:
    """The file: the cited sources numbered again from s1 in the order they were given."""
    cited = {item.source for _, item in labelled}
    kept = [source for source in sources if source.id in cited]
    new_id = {source.id: f"s{number}" for number, source in enumerate(kept, 1)}
    fields = {entry.id: entry for entry in reply.sources}
    entries = tuple(
        SourceEntry(
            new_id[source.id],
            source.page.url,
            fields[source.id].publisher,
            source.page.published or "unknown",
            accessed,
            fields[source.id].lang,
        )
        for source in kept
    )
    sections = tuple(
        Section(
            section.heading,
            tuple(
                Item(item.text.strip(), new_id[item.source]) for item in section.items
            ),
            tuple(note.strip() for note in section.notes),
        )
        for section in reply.sections
        if section.items or section.notes
    )
    file = TruthFile(
        title=reply.title.strip(),
        event_date=day,
        event_time=reply.event_time,
        targets=tuple(dict.fromkeys(reply.targets)),
        markets=tuple(dict.fromkeys(reply.markets)),
        tickers=tuple(reply.tickers),
        exposure=tuple(dict.fromkeys(reply.exposure)),
        significance=reply.significance,
        significance_reason=reply.significance_reason.strip(),
        keyword_groups=tuple(tuple(group) for group in reply.keyword_groups),
        sources=entries,
        sections=sections,
    )
    passages = tuple(
        (label, Item(item.text.strip(), new_id[item.source]), item.passage)
        for label, item in labelled
    )
    conversions = tuple(
        Conversion(one.original, one.converted, one.note) for one in reply.conversions
    )
    return Record(file, reply.slug, passages, conversions)
