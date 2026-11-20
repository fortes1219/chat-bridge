"""Requests the chat service refuses before it searches, so neither the search nor the model runs."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat import service
from chat_bridge.chat.schemas import MAX_QUESTION_LENGTH
from chat_bridge.chat.server import create_app

QUESTION = b'{"question": "x"}'


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A client of the app at 127.0.0.1, where reaching the search fails the test."""

    async def no_search(question: str) -> list[service.FoundSection]:
        raise AssertionError(f"the search ran for {question!r}")

    monkeypatch.setattr(service, "find_sections", no_search)
    with TestClient(create_app(), base_url="http://127.0.0.1") as test_client:
        yield test_client


def test_a_request_without_a_json_content_type_is_refused(client: TestClient) -> None:
    response = client.post("/chat/stream", content=QUESTION)

    assert response.status_code == 422


def test_a_request_with_a_text_content_type_is_refused(client: TestClient) -> None:
    response = client.post(
        "/chat/stream", content=QUESTION, headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "host", ["evil.example", "evil.example:8000", "127.0.0.1.evil.example"]
)
def test_a_request_for_another_host_is_refused(client: TestClient, host: str) -> None:
    response = client.post(
        "/chat/stream", json={"question": "x"}, headers={"host": host}
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "question",
    [
        pytest.param("", id="empty"),
        pytest.param("問" * (MAX_QUESTION_LENGTH + 1), id="over the limit"),
    ],
)
def test_a_question_outside_the_limits_is_refused(
    client: TestClient, question: str
) -> None:
    response = client.post("/chat/stream", json={"question": question})

    assert response.status_code == 422


def test_no_cross_origin_access_is_granted(client: TestClient) -> None:
    response = client.options(
        "/chat/stream",
        headers={
            "origin": "https://evil.example",
            "access-control-request-method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers
