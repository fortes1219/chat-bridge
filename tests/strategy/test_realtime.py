"""The real-time connection, through the app as the page reaches it, over Engine.IO's long polling.

The store is stubbed and the prices come from a stand-in: no database, no network.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat.server import create_app
from chat_bridge.strategy import store
from chat_bridge.strategy.schemas import StoredStrategy
from chat_bridge.strategy.state import STATE
from tests.strategy.test_state import STORED, _Prices, _quote

PAGE = "http://127.0.0.1"
POLLING = "/socket.io/?EIO=4&transport=polling"
# Engine.IO separates the packets of one long-polling reply with this character.
SEPARATOR = "\x1e"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    async def read() -> StoredStrategy:
        return STORED

    monkeypatch.setattr(store, "read_strategy", read)
    app = create_app(prices=_Prices(_quote("1480")))
    with TestClient(app, base_url=PAGE) as test_client:
        yield test_client


def _open(client: TestClient) -> str:
    """Open an Engine.IO session and join Socket.IO's default namespace; the session id."""
    handshake = client.get(POLLING, headers={"Origin": PAGE})
    assert handshake.status_code == 200
    sid = str(json.loads(handshake.text[1:])["sid"])
    joined = client.post(
        f"{POLLING}&sid={sid}",
        content="40",
        headers={"Origin": PAGE, "Content-Type": "text/plain;charset=UTF-8"},
    )
    assert joined.text == "OK"
    return sid


def _next_strategy(client: TestClient, sid: str) -> dict[str, Any]:
    """The next `strategy` event the session receives."""
    for _ in range(5):
        reply = client.get(f"{POLLING}&sid={sid}", headers={"Origin": PAGE})
        for packet in reply.text.split(SEPARATOR):
            if packet.startswith("42"):
                name, view = json.loads(packet[2:])
                assert name == "strategy"
                return dict(view)
    raise AssertionError("no strategy event arrived")


def test_the_page_gets_the_strategy_with_its_prices_when_it_connects(
    client: TestClient,
) -> None:
    view = _next_strategy(client, _open(client))

    assert view["valuation"]["holdings"][0]["price"] == "1480"
    assert view["notice"] == store.SAMPLE_NOTICE


def test_a_new_price_is_sent_to_the_open_page(client: TestClient) -> None:
    sid = _open(client)
    _next_strategy(client, sid)

    assert client.portal is not None
    client.portal.call(STATE.price, _quote("1490", minute=31))

    view = _next_strategy(client, sid)
    assert view["valuation"]["holdings"][0]["price"] == "1490"


def test_another_web_page_cannot_open_the_connection(client: TestClient) -> None:
    reply = client.get(POLLING, headers={"Origin": "http://news.example"})

    assert reply.status_code == 400


def test_a_host_name_other_than_this_machine_is_refused(client: TestClient) -> None:
    reply = client.get(POLLING, headers={"Host": "rebound.example", "Origin": PAGE})

    assert reply.status_code == 400
