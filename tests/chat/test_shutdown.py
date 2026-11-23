"""The chat service stops the embedded database when it shuts down.

It starts a real embedded database, so the test is marked slow.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from chat_bridge.chat.server import create_app
from chat_bridge.database import pgdata_dir
from tests.utils import prepare_local_data, using_local_data

pytestmark = pytest.mark.slow


def test_shutting_down_the_service_stops_the_database(tmp_path: Path) -> None:
    with using_local_data(prepare_local_data(tmp_path / "local_data")):
        with TestClient(create_app(), base_url="http://127.0.0.1") as client:
            # Reading the records starts the database.
            assert client.get("/chat/records").status_code == 200
            assert (pgdata_dir() / "postmaster.pid").exists()

        # PostgreSQL removes postmaster.pid when it stops.
        assert not (pgdata_dir() / "postmaster.pid").exists()
