"""A knowledge base of all 71 sample files, ingested once for the search tests that need it."""

from collections.abc import Iterator

import pytest

from tests.utils import TRUTH_DIR, ingest, prepare_local_data, using_local_data


@pytest.fixture(scope="package")
def sample_knowledge_base(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    folder = prepare_local_data(tmp_path_factory.mktemp("sample_local_data"))
    with using_local_data(folder):
        report = ingest(TRUTH_DIR)
        assert not report.rejected
        yield
