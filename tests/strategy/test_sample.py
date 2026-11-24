"""The sample profile in the repository, and the checks a sample must pass before it is loaded."""

import json
from pathlib import Path
from typing import Any

import pytest

from chat_bridge.strategy.sample import SampleProfileError, read_sample

SAMPLE = json.loads(
    (Path(__file__).parents[2] / "data" / "profile" / "sample.json").read_text(
        encoding="utf-8"
    )
)


def test_the_repositorys_sample_passes_and_says_it_is_simulated() -> None:
    sample = read_sample()

    assert "simulated" in sample.about
    assert sum(sample.targets.values()) == 100
    assert [holding.symbol for holding in sample.holdings][-1] == "CASH"
    assert {holding.market for holding in sample.holdings} == {"TW", "US", None}


def _broken(tmp_path: Path, change: dict[str, Any]) -> Path:
    path = tmp_path / "sample.json"
    path.write_text(json.dumps({**SAMPLE, **change}), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "change",
    [
        {"targets": {**SAMPLE["targets"], "CASH": 11}},
        {
            "targets": {
                key: value for key, value in SAMPLE["targets"].items() if key != "CASH"
            }
        },
        {"targets": {**SAMPLE["targets"], "TSLA": 0}},
        {
            "rules": [
                {
                    "kind": "best_return",
                    "limit_percent": 10,
                    "market": None,
                    "enabled": True,
                }
            ]
        },
        {
            "rules": [
                {
                    "kind": "max_holding_weight",
                    "limit_percent": 120,
                    "market": None,
                    "enabled": True,
                }
            ]
        },
        {"holdings": [*SAMPLE["holdings"], {**SAMPLE["holdings"][0]}]},
        {"note": "an extra field"},
    ],
)
def test_a_sample_that_breaks_a_check_is_not_loaded(
    tmp_path: Path, change: dict[str, Any]
) -> None:
    with pytest.raises(SampleProfileError):
        read_sample(_broken(tmp_path, change))


def test_a_missing_sample_file_is_said(tmp_path: Path) -> None:
    with pytest.raises(SampleProfileError):
        read_sample(tmp_path / "missing.json")
