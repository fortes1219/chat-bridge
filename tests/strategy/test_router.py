"""The strategy endpoints, with the store stubbed: no database is read.

Accepting or rejecting must come from the page itself. A form or a plain-text post, which another
web page can send without the browser asking the service first, is refused and changes nothing.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat.server import create_app
from chat_bridge.strategy import store
from chat_bridge.strategy.schemas import StoredStrategy

STORED = StoredStrategy(
    holdings=[],
    targets=[],
    proposal=None,
    notice=store.SAMPLE_NOTICE,
)
DECISION = "/strategy/proposals/1/decision"


@pytest.fixture
def decisions(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, str]]:
    made: list[tuple[int, str]] = []

    async def decide(proposal_id: int, decision: str) -> StoredStrategy:
        made.append((proposal_id, decision))
        return STORED

    async def read() -> StoredStrategy:
        return STORED

    monkeypatch.setattr(store, "decide", decide)
    monkeypatch.setattr(store, "read_strategy", read)
    return made


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def test_the_strategy_is_read(client: TestClient, decisions: list[Any]) -> None:
    response = client.get("/strategy")

    assert response.status_code == 200
    assert response.json()["notice"] == store.SAMPLE_NOTICE


@pytest.mark.parametrize("decision", ["accept", "reject"])
def test_a_json_decision_is_made(
    client: TestClient, decisions: list[Any], decision: str
) -> None:
    response = client.post(DECISION, json={"decision": decision})

    assert response.status_code == 200
    assert decisions == [(1, decision)]


@pytest.mark.parametrize(
    "send",
    [
        {"data": {"decision": "accept"}},
        {
            "content": '{"decision": "accept"}',
            "headers": {"Content-Type": "text/plain"},
        },
        {
            "content": '{"decision": "accept"}',
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        },
        {"content": "", "headers": {"Content-Type": "multipart/form-data; boundary=x"}},
        {},
    ],
)
def test_a_post_another_page_can_send_without_asking_is_refused_and_changes_nothing(
    client: TestClient, decisions: list[Any], send: dict[str, Any]
) -> None:
    response = client.post(DECISION, **send)

    assert response.status_code == 422
    assert decisions == []


@pytest.mark.parametrize(
    "body", [{"decision": "approve"}, {"decision": "accept", "targets": {"CASH": 100}}]
)
def test_an_unknown_decision_or_any_other_field_is_refused(
    client: TestClient, decisions: list[Any], body: dict[str, Any]
) -> None:
    response = client.post(DECISION, json=body)

    assert response.status_code == 422
    assert decisions == []


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (store.ProposalNotFoundError(1), 404, "proposal_not_found"),
        (store.ProposalNotOpenError(1, "accepted"), 409, "proposal_not_open"),
    ],
)
def test_a_decision_on_a_proposal_that_is_gone_or_closed_is_refused_with_its_code(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: store.StrategyError,
    status: int,
    code: str,
) -> None:
    async def refuse(proposal_id: int, decision: str) -> StoredStrategy:
        raise error

    monkeypatch.setattr(store, "decide", refuse)

    response = client.post(DECISION, json={"decision": "accept"})

    assert response.status_code == status
    assert response.json()["detail"]["code"] == code


def test_a_missing_profile_is_said_with_its_code(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def missing() -> StoredStrategy:
        raise store.ProfileMissingError()

    monkeypatch.setattr(store, "read_strategy", missing)

    response = client.get("/strategy")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "profile_missing"
