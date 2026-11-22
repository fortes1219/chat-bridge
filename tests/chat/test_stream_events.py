"""What `POST /chat/stream` sends, as Server-Sent Events, without searching or starting a model."""

import json
from collections.abc import AsyncIterator, Iterator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat import service
from chat_bridge.chat.programs import Program
from chat_bridge.chat.schemas import ChatContext, ChatDelta, Source
from chat_bridge.chat.server import create_app
from chat_bridge.errors import LocalSetupError

SECTION = service.FoundSection(
    section_id=7,
    source=Source(
        number=1,
        file="data/truth/a.md",
        title="T",
        heading="H",
        event_date=None,
    ),
    text="section text",
    score=0.03,
)
CONTEXT = ChatDelta(
    type="response.context",
    context=ChatContext(
        sources=[SECTION.source],
        data_latest_date=date(2026, 9, 17),
        disclaimer="notice",
        program=Program.CODEX,
    ),
)


def _events(body: str) -> list[dict[str, Any]]:
    """Each event of a text/event-stream body: its name, if any, and its data as JSON."""
    events: list[dict[str, Any]] = []
    for block in body.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "data" in fields:
            events.append(
                {"event": fields.get("event"), "data": json.loads(fields["data"])}
            )
    return events


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    async def found(question: str) -> list[service.FoundSection]:
        return [SECTION]

    monkeypatch.setattr(service, "find_sections", found)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def test_the_context_and_each_piece_are_one_unnamed_event_each(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def answer(*args: Any) -> AsyncIterator[ChatDelta]:
        yield CONTEXT
        yield ChatDelta(type="response.output_text.delta", delta="聯準會")
        yield ChatDelta(type="response.output_text.delta", delta="降息。")

    monkeypatch.setattr(service, "answer_stream", answer)

    response = client.post("/chat/stream", json={"question": "q"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(response.text)
    assert [event["event"] for event in events] == [None, None, None]
    assert events[0]["data"]["type"] == "response.context"
    assert events[0]["data"]["context"]["sources"][0]["event_date"] is None
    assert [event["data"]["delta"] for event in events[1:]] == ["聯準會", "降息。"]


def test_an_error_after_the_start_is_a_last_event_named_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def answer(*args: Any) -> AsyncIterator[ChatDelta]:
        yield CONTEXT
        raise RuntimeError("the program stopped")

    monkeypatch.setattr(service, "answer_stream", answer)

    response = client.post("/chat/stream", json={"question": "q"})

    events = _events(response.text)
    assert events[0]["data"]["type"] == "response.context"
    assert events[-1] == {"event": "error", "data": {"message": "the program stopped"}}


def test_a_search_that_cannot_run_is_an_http_error_not_an_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def no_database(question: str) -> list[service.FoundSection]:
        raise LocalSetupError("the knowledge base is empty")

    monkeypatch.setattr(service, "find_sections", no_database)
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        response = client.post("/chat/stream", json={"question": "q"})

    assert response.status_code == 503
    assert response.json() == {"detail": "the knowledge base is empty"}
