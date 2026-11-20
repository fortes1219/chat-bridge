"""The search command's arguments, checked before the database starts."""

import pytest

from chat_bridge.cli import EXIT_ERROR, main
from chat_bridge.search.cli import MAX_LIMIT, MIN_LIMIT, _limit


@pytest.mark.parametrize(
    ("value", "message"),
    [
        pytest.param(
            str(MIN_LIMIT - 1), "must be from 1 to 10000", id="below the range"
        ),
        pytest.param(
            str(MAX_LIMIT + 1), "must be from 1 to 10000", id="above the range"
        ),
        pytest.param(
            "99999999999999999999", "must be from 1 to 10000", id="past bigint"
        ),
        pytest.param("five", "not a whole number", id="not a number"),
    ],
)
def test_a_limit_outside_the_range_is_refused(
    value: str, message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["search", "台積電", "--limit", value])

    assert raised.value.code == EXIT_ERROR
    assert message in capsys.readouterr().err


@pytest.mark.parametrize("value", [MIN_LIMIT, MAX_LIMIT])
def test_the_ends_of_the_range_are_accepted(value: int) -> None:
    assert _limit(str(value)) == value
