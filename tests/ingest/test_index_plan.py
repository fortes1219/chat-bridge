"""What an ingest run rebuilds: only the part of the index that changed."""

import pytest

from chat_bridge.ingest.service import IndexUpdate, _plan


@pytest.mark.parametrize(
    ("entries_are_current", "words_are_current", "has_new_documents", "expected"),
    [
        pytest.param(False, True, False, IndexUpdate.ALL, id="model or layout changed"),
        pytest.param(
            False, False, True, IndexUpdate.ALL, id="model changed with words"
        ),
        pytest.param(True, False, False, IndexUpdate.KEYWORDS, id="words changed"),
        pytest.param(
            True, False, True, IndexUpdate.KEYWORDS, id="words and files changed"
        ),
        pytest.param(True, True, True, IndexUpdate.WRITTEN_FILES, id="files changed"),
        pytest.param(True, True, False, IndexUpdate.NONE, id="nothing changed"),
    ],
)
def test_only_what_changed_is_rebuilt(
    entries_are_current: bool,
    words_are_current: bool,
    has_new_documents: bool,
    expected: IndexUpdate,
) -> None:
    assert _plan(entries_are_current, words_are_current, has_new_documents) == expected
