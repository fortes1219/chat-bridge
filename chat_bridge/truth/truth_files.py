"""The folder of truth files: what it already has, and a checked record written into it in the
layout of the sample files.

The front matter is written with ruamel.yaml as the sample files are: flow lists for targets,
markets, tickers and exposure, one flow list per keyword group, and a block list of sources; a
value that YAML would read as something other than text is double-quoted (`"2330"`). A file goes
into the folder whole: it is written beside its final name and renamed onto it, so a run stopped
part way leaves no half file.
"""

from __future__ import annotations

import io
import os
import re
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from chat_bridge.collect.news_files import CLOSING_LINE
from chat_bridge.config import PROJECT_ROOT

TRUTH_FOLDER = PROJECT_ROOT / "data" / "truth"
CONVERSIONS_FILE = PROJECT_ROOT / "tests" / "data" / "number_conversions.md"
_DATED_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
# A source the news cites, as opposed to a data source the program adds ("d1").
SOURCE_PREFIX = "s"
PART_SUFFIX = ".part"
FULL_WIDTH_ENDS = ("。", "」", "）")


@dataclass(frozen=True)
class FolderEvent:
    path: Path
    event_date: date
    title: str
    # The pages its news sources cite.
    urls: frozenset[str]


@dataclass(frozen=True)
class SourceEntry:
    """A source as the file lists it."""

    id: str
    url: str
    publisher: str
    published: date | str
    accessed: date
    lang: str
    format: str = "html"


@dataclass(frozen=True)
class Item:
    text: str
    source: str


@dataclass(frozen=True)
class Section:
    heading: str
    items: tuple[Item, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TruthFile:
    """What a file holds, in the order it is written."""

    title: str
    event_date: date
    event_time: str | None
    targets: tuple[int, ...]
    markets: tuple[str, ...]
    tickers: tuple[str, ...]
    exposure: tuple[str, ...]
    significance: str
    significance_reason: str
    keyword_groups: tuple[tuple[str, ...], ...]
    sources: tuple[SourceEntry, ...]
    sections: tuple[Section, ...]


def _name_date(path: Path) -> date | None:
    match = _DATED_NAME.match(path.name)
    try:
        return date.fromisoformat(match.group(1)) if match else None
    except ValueError:
        return None


def _dated_files(folder: Path) -> list[tuple[date, Path]]:
    if not folder.is_dir():
        return []
    found = [(_name_date(path), path) for path in folder.glob("*.md")]
    return sorted((day, path) for day, path in found if day is not None)


def latest_date(folder: Path) -> date | None:
    """The latest event date of the folder, by its file names."""
    files = _dated_files(folder)
    return files[-1][0] if files else None


def example(folder: Path) -> str | None:
    """The latest file of the folder, given to the agent as an example of the format."""
    files = _dated_files(folder)
    return files[-1][1].read_text(encoding="utf-8") if files else None


def _front(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    loaded = yaml.safe_load(text.split("---\n", 2)[1])
    return loaded if isinstance(loaded, dict) else {}


def folder_events(folder: Path, start: date | None) -> list[FolderEvent]:
    """The folder's files dated on or after `start` (all of them with no start), read for their
    title and the pages they cite. Only those files are read, so the cost grows with the run."""
    events: list[FolderEvent] = []
    for day, path in _dated_files(folder):
        if start is not None and day < start:
            continue
        front = _front(path)
        sources = front.get("sources")
        urls = frozenset(
            str(entry.get("url", ""))
            for entry in (sources if isinstance(sources, list) else [])
            if isinstance(entry, dict)
            and str(entry.get("id", "")).startswith(SOURCE_PREFIX)
        )
        events.append(FolderEvent(path, day, str(front.get("title", "")), urls))
    return events


def free_path(folder: Path, event_date: date, slug: str) -> Path:
    """`YYYY-MM-DD-slug.md`, with a number when the name is taken."""
    path = folder / f"{event_date.isoformat()}-{slug}.md"
    number = 2
    while path.exists():
        path = folder / f"{event_date.isoformat()}-{slug}-{number}.md"
        number += 1
    return path


def _yaml() -> YAML:
    yaml_rt = YAML(typ="rt")
    # As the sample files are written: "sources:\n  - id: s1\n    url: …", no wrapping.
    yaml_rt.indent(mapping=2, sequence=4, offset=2)
    yaml_rt.width = 4096
    # Each source's `accessed` is the same day: written out each time, as the sample files have
    # it, not as an anchor and aliases.
    yaml_rt.representer.ignore_aliases = lambda *data: True
    return yaml_rt


def _text(value: str) -> str:
    """The value, double-quoted when YAML would read it as something other than this text."""
    try:
        read = yaml.safe_load(value)
    except yaml.YAMLError:
        read = None
    return value if read == value else DoubleQuotedScalarString(value)


def _flow(values: Iterable[Any]) -> CommentedSeq:
    seq = CommentedSeq(values)
    seq.fa.set_flow_style()
    return seq


def _source(entry: SourceEntry) -> CommentedMap:
    published = (
        entry.published if isinstance(entry.published, date) else _text(entry.published)
    )
    return CommentedMap(
        [
            ("id", entry.id),
            ("url", _text(entry.url)),
            ("publisher", _text(entry.publisher)),
            ("published", published),
            ("accessed", entry.accessed),
            ("lang", _text(entry.lang)),
            ("format", entry.format),
        ]
    )


def front_matter(file: TruthFile) -> str:
    """The front matter's lines, between the two "---" lines."""
    fields = CommentedMap()
    fields["title"] = _text(file.title)
    fields["event_date"] = file.event_date
    if file.event_time is not None:
        fields["event_time"] = _text(file.event_time)
    fields["targets"] = _flow(file.targets)
    fields["markets"] = _flow(_text(market) for market in file.markets)
    fields["tickers"] = _flow(_text(ticker) for ticker in file.tickers)
    fields["exposure"] = _flow(file.exposure)
    fields["significance"] = file.significance
    fields["keyword_groups"] = CommentedSeq(
        _flow(_text(name) for name in group) for group in file.keyword_groups
    )
    fields["sources"] = CommentedSeq(_source(entry) for entry in file.sources)
    out = io.StringIO()
    _yaml().dump(fields, out)
    return out.getvalue()


def _item_line(item: Item) -> str:
    """The sample files put the source mark right after a full-width closing mark (166 items) and
    one space after anything else (344 items)."""
    gap = "" if item.text.endswith(FULL_WIDTH_ENDS) else " "
    return f"- {item.text}{gap}[{item.source}]"


def _section_lines(section: Section) -> list[str]:
    lines = [f"## {section.heading}", ""]
    lines += [_item_line(item) for item in section.items]
    if section.items:
        lines.append("")
    for note in section.notes:
        lines += [f"> {note}", ""]
    return lines


def render(file: TruthFile) -> str:
    """The whole file: front matter, the sections, and the significance line."""
    lines = ["---", *front_matter(file).rstrip("\n").split("\n"), "---", ""]
    for section in file.sections:
        lines += _section_lines(section)
    lines.append(f"{CLOSING_LINE}（{file.significance}）：{file.significance_reason}")
    return "\n".join(lines) + "\n"


def put(path: Path, text: str) -> None:
    """Write the file beside its name and rename it onto the name, so it appears whole."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, part = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.stem}-", suffix=PART_SUFFIX
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as out:
            out.write(text)
        os.replace(part, path)
    except BaseException:
        Path(part).unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class Conversion:
    original: str
    converted: str
    note: str


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def add_conversions(
    record_file: Path, file_stem: str, conversions: Iterable[Conversion]
) -> int:
    """Add each conversion as a row of the record of conversions, unless the row is there
    already (a run after one stopped part way adds no row twice). The number of rows added."""
    existing = record_file.read_text(encoding="utf-8") if record_file.exists() else ""
    # An empty note is written "| |", as the record's earlier rows are.
    rows = [
        f"| {file_stem} | {_cell(one.original)} | {_cell(one.converted)} |"
        + (f" {_cell(one.note)} |" if one.note.strip() else " |")
        for one in conversions
    ]
    new = [row for row in dict.fromkeys(rows) if row not in existing.split("\n")]
    if not new:
        return 0
    joined = "\n".join(new) + "\n"
    text = existing + ("" if existing.endswith("\n") or not existing else "\n") + joined
    record_file.write_text(text, encoding="utf-8", newline="\n")
    return len(new)
