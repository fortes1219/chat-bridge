"""The knowledge base keeps each event's markets and moment, not its market table.

Ingesting runs the real embedding model and the embedded database, so these tests are marked
slow.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select

from chat_bridge.cli import main
from chat_bridge.database import open_engine
from chat_bridge.ingest.models import Document, Section
from chat_bridge.ingest.service import MARKET_SECTION, is_market_section
from tests.utils import copy_sample_files, ingest, prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

SAMPLE_FILES = (
    "2026-09-16-fomc-raises-rate.md",
    "2026-11-06-taiex-plunges-1873-points.md",
)
TIMED_FILE = "2026-11-18-fed-minutes.md"
TIMED_FRONT = (
    "---\n"
    "title: 會議紀錄\n"
    "event_date: 2026-11-18\n"
    "event_time: 2026-11-18T14:00:00-05:00\n"
    "markets: [US, TW]\n"
    "---\n\n"
    "## 事件發生\n\n聯準會公布會議紀錄。\n"
)


async def _stored() -> tuple[list[Any], list[str]]:
    async with open_engine() as engine, engine.connect() as connection:
        documents = (
            await connection.execute(
                select(Document.source_path, Document.markets, Document.event_time)
            )
        ).all()
        headings = (await connection.execute(select(Section.heading))).scalars().all()
    return list(documents), list(headings)


def test_market_sections_are_not_stored_and_each_events_timing_is(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = copy_sample_files(tmp_path / "truth", SAMPLE_FILES)
    (folder / TIMED_FILE).write_text(TIMED_FRONT, encoding="utf-8", newline="\n")

    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        report = ingest(folder)
        documents, headings = asyncio.run(_stored())
        (folder / "2026-11-19-note.md").write_text(
            "---\nevent_date: 2026-11-19\n---\n\n## 事件發生\n\n筆記。\n\n"
            f"## {MARKET_SECTION}\n\n| a |\n|---|\n| 1 |\n",
            encoding="utf-8",
            newline="\n",
        )
        main(["ingest", str(folder)])

    assert report.market_sections_left_out == len(SAMPLE_FILES)
    assert not [heading for heading in headings if is_market_section(heading)]
    timing = {path: (markets, moment) for path, markets, moment in documents}
    assert timing["2026-09-16-fomc-raises-rate.md"] == (["US"], None)
    assert timing[TIMED_FILE] == (
        ["US", "TW"],
        datetime(2026, 11, 18, 14, 0, tzinfo=timezone(timedelta(hours=-5))),
    )
    assert (
        f"Not stored: 1 sections headed {MARKET_SECTION}; the chat looks market prices "
        "up instead." in capsys.readouterr().out
    )
