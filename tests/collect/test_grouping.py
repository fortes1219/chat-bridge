"""Pages given as addresses, sorted into events by a stand-in agent's answer."""

from datetime import date

from chat_bridge.collect.grouping import groups_schema, numbered, question, read_groups
from chat_bridge.collect.record import Window
from chat_bridge.collect.rules import read_rules
from tests.collect.stand_ins import CNA, FED

PAGES = numbered((FED, CNA))
WINDOW = Window(None, date(2026, 11, 25))


def test_the_question_gives_the_targets_and_each_page_as_data() -> None:
    text = question(PAGES, read_rules(), WINDOW)

    assert text.startswith("Sort these pages into events from any date to 2026-11-25.")
    assert f'<page id="p1" url="{FED.url}"' in text and CNA.text in text
    assert groups_schema(list(PAGES))["properties"]["not_events"]["items"][
        "properties"
    ]["page"]["enum"] == ["p1", "p2"]


def test_events_get_their_pages_and_a_page_in_no_event_is_named() -> None:
    reply = {
        "events": [
            {"event_date": "2026-11-24", "about": "Fed holds", "pages": ["p1", "p9"]},
            {"event_date": "2026-11-28", "about": "too late", "pages": ["p2"]},
        ],
        "not_events": [{"page": "p2", "reason": "a coffee chain's prices"}],
    }

    groups = read_groups(reply, PAGES, WINDOW)

    assert [(one.about, one.pages) for one in groups.events] == [("Fed holds", (FED,))]
    assert groups.refused == (
        ("too late", "its date 2026-11-28 is outside the asked dates"),
        (CNA.url, "bears on no collection target: a coffee chain's prices"),
    )
