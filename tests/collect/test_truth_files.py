"""A file written in the sample files' layout: the 71 files' own values give back their bytes."""

import re
from pathlib import Path

import pytest
import yaml

from chat_bridge.collect.truth_files import (
    TRUTH_FOLDER,
    Item,
    Section,
    SourceEntry,
    TruthFile,
    front_matter,
    render,
)

SAMPLES = sorted(TRUTH_FOLDER.glob("*.md"))
_ITEM = re.compile(r"^- (.*?) ?\[(s\d+)\]$")


def _file(front: dict[str, object], sections: tuple[Section, ...] = ()) -> TruthFile:
    sources = [
        entry
        for entry in front["sources"]  # type: ignore[attr-defined]
        if str(entry["id"]).startswith("s")
    ]
    return TruthFile(
        title=str(front["title"]),
        event_date=front["event_date"],  # type: ignore[arg-type]
        event_time=None,
        targets=tuple(front["targets"]),  # type: ignore[call-overload]
        markets=tuple(front["markets"]),  # type: ignore[call-overload]
        tickers=tuple(str(one) for one in front["tickers"]),  # type: ignore[attr-defined]
        exposure=tuple(front["exposure"]),  # type: ignore[call-overload]
        significance=str(front["significance"]),
        significance_reason="",
        keyword_groups=tuple(
            tuple(str(name) for name in group)
            for group in front["keyword_groups"]  # type: ignore[attr-defined]
        ),
        sources=tuple(
            SourceEntry(
                entry["id"],
                entry["url"],
                entry["publisher"],
                entry["published"],
                entry["accessed"],
                entry["lang"],
                entry["format"],
            )
            for entry in sources
        ),
        sections=sections,
    )


@pytest.mark.parametrize("path", SAMPLES, ids=[path.stem for path in SAMPLES])
def test_a_sample_files_front_matter_is_written_back_byte_for_byte(path: Path) -> None:
    head = path.read_text(encoding="utf-8").split("---\n", 2)[1]

    written = front_matter(_file(yaml.safe_load(head)))

    # The news sources; the data sources (d1, d2) are the market section's, written after.
    assert written == head.split("  - id: d")[0]


def test_every_sample_item_line_is_written_back() -> None:
    lines = [
        line
        for path in SAMPLES
        for line in path.read_text(encoding="utf-8").split("\n")
        if _ITEM.match(line)
    ]
    items = []
    for line in lines:
        match = _ITEM.match(line)
        assert match is not None
        items.append(Item(match.group(1), match.group(2)))
    front = yaml.safe_load(SAMPLES[0].read_text(encoding="utf-8").split("---\n", 2)[1])

    text = render(_file(front, (Section("事件發生", tuple(items), ()),)))

    assert len(lines) == 510
    assert [line for line in text.split("\n") if _ITEM.match(line)] == lines
