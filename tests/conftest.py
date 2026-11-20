"""Fixtures for every test.

No test touches the project's own local_data: the whole run gets a data folder of its own,
as the Azure rag-postgres sample points its tests at their own database settings for the
session. The embedding model is the one exception, because it is 2.3 GB: when the project
has already downloaded it, the run reads it from there through huggingface_hub's own
HF_HUB_CACHE setting.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from chat_bridge.embedding import HUB_CACHE_ENV
from tests.utils import PROJECT_LOCAL_DATA, prepare_local_data, using_local_data


@pytest.fixture(scope="session", autouse=True)
def session_local_data(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    folder = prepare_local_data(tmp_path_factory.mktemp("local_data"))
    project_models = PROJECT_LOCAL_DATA / "models"
    with pytest.MonkeyPatch.context() as patch, using_local_data(folder):
        if HUB_CACHE_ENV not in os.environ and project_models.is_dir():
            patch.setenv(HUB_CACHE_ENV, str(project_models))
        yield folder
