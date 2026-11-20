"""Search yield on the sample data: the 41 questions must not do worse than the baseline.

This needs the embedding model and the embedded database, and ingesting the 71 sample files
takes minutes, so it is marked slow.
"""

import asyncio
import operator
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel, ConfigDict

from chat_bridge.ingest.service import ingest_folder
from chat_bridge.search.service import SearchHit, search
from tests.utils import TRUTH_DIR, prepare_local_data, using_local_data

pytestmark = pytest.mark.slow

CASES_FILE = Path(__file__).parents[1] / "data" / "search_yield.yaml"

# How each measured number must compare with its baseline.
CHECKS: dict[str, Callable[[int, int], bool]] = {
    "target_good": operator.ge,
    "target_market": operator.le,
    "regression_first": operator.ge,
    "regression_top3": operator.ge,
    "not_in_data_empty": operator.ge,
}


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    question: str
    files: list[str]


class Baseline(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target_good: int
    target_market: int
    regression_first: int
    regression_top3: int
    not_in_data_empty: int


class YieldCases(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    top: int
    market_heading: str
    baseline: Baseline
    files: dict[str, list[str]]
    target: list[Case]
    regression: list[Case]
    not_in_data: list[str]


@pytest.fixture(scope="module")
def knowledge_base(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    folder = prepare_local_data(tmp_path_factory.mktemp("yield_local_data"))
    with using_local_data(folder):
        report = asyncio.run(ingest_folder(TRUTH_DIR))
        assert not report.rejected
        yield


def hits_for(question: str, top: int) -> list[SearchHit]:
    return asyncio.run(search(question, top)).hits


def is_expected(hit: SearchHit, files: list[str]) -> bool:
    return any(hit.source_path.startswith(prefix) for prefix in files)


def measure(cases: YieldCases) -> tuple[dict[str, int], list[str]]:
    """The yield numbers, and one line per question to explain a failure."""
    measured = dict.fromkeys(CHECKS, 0)
    details: list[str] = []

    for case in cases.target:
        hits = hits_for(case.question, cases.top)
        market = [hit for hit in hits if cases.market_heading in hit.heading]
        good = [
            hit for hit in hits if hit not in market and is_expected(hit, case.files)
        ]
        measured["target_good"] += len(good)
        measured["target_market"] += len(market)
        details.append(
            f"target {case.question}: good {len(good)}, market {len(market)}"
        )

    for case in cases.regression:
        hits = hits_for(case.question, cases.top)
        first = bool(hits) and is_expected(hits[0], case.files)
        in_top3 = any(is_expected(hit, case.files) for hit in hits[:3])
        measured["regression_first"] += first
        measured["regression_top3"] += in_top3
        top_path = hits[0].source_path if hits else None
        details.append(
            f"regression {case.question}: first {first}, top 3 {in_top3}, got {top_path}"
        )

    for question in cases.not_in_data:
        hits = hits_for(question, cases.top)
        measured["not_in_data_empty"] += not hits
        details.append(f"not in data {question}: {len(hits)} hits")

    return measured, details


def test_search_yield_does_not_fall_below_the_baseline(knowledge_base: None) -> None:
    cases = YieldCases.model_validate(
        yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    )
    baseline = cases.baseline.model_dump()

    measured, details = measure(cases)
    # Shown with `pytest -rP`, so a passing run still reports how far above the baseline it is.
    print("measured:", measured, "baseline:", baseline)

    failures = [
        f"{name}: measured {measured[name]}, baseline {baseline[name]}"
        for name, holds in CHECKS.items()
        if not holds(measured[name], baseline[name])
    ]
    assert not failures, "\n".join([*failures, *details])
