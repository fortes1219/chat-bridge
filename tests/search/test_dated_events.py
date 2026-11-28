"""The events of some days, taken by their stored event date, and their first sections: what a
short price lookup brings to the program when the question's words find none of them.

Ingesting needs the embedding model and the embedded database, so the test is marked slow.
"""

import asyncio
from datetime import date
from pathlib import Path

import pytest

from chat_bridge.search.service import dated_events, first_sections
from tests.utils import copy_sample_files, ingest, prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

FED = "2026-09-16-fomc-raises-rate.md"
CENTRAL_BANK = "2026-09-17-cbc-holds-rates-eases-mortgage-cap.md"
YIELD = "2026-09-14-10-year-yield-tops-5-percent.md"
TECH = "2026-09-14-tech-selloff-after-ai-slowdown-call.md"
CHIPS = "2026-09-10-trump-chip-tariff-remarks-moea-response.md"


def test_the_events_of_each_span_come_in_date_order_and_only_kept_ones_are_read(
    tmp_path: Path,
) -> None:
    files = (CHIPS, YIELD, TECH, FED, CENTRAL_BANK)
    folder = copy_sample_files(tmp_path / "truth", files)
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        assert not ingest(folder).rejected

        # Two spans apart: the 14 September files between them are not read.
        events = asyncio.run(
            dated_events(
                [
                    (date(2026, 9, 10), date(2026, 9, 10)),
                    (date(2026, 9, 16), date(2026, 9, 17)),
                ]
            )
        )
        sections = asyncio.run(first_sections([CENTRAL_BANK, FED]))

    assert [(e.source_path, e.markets) for e in events] == [
        (CHIPS, ("TW",)),
        (FED, ("US",)),
        (CENTRAL_BANK, ("TW",)),
    ]
    # In the order asked, each by its first section.
    assert [(s.source_path, s.heading) for s in sections] == [
        (CENTRAL_BANK, "事件發生"),
        (FED, "事件發生"),
    ]
