"""The person's rules: each kind checked on target weights, and the rules a save refuses.

No database is read: the checks are computed from fixed holdings and targets.
"""

from typing import Any, get_args

import pytest

from chat_bridge.strategy import store
from chat_bridge.strategy.compute import RULE_MEASURES, rule_checks
from chat_bridge.strategy.schemas import (
    Market,
    RuleInput,
    RuleKind,
    RuleView,
    StrategyErrorCode,
)
from tests.strategy.test_valuation import _holding

HOLDINGS = [
    _holding("2330.TW", "TW", "TWD", "2000", "1980"),
    _holding("0050.TW", "TW", "TWD", "20000", "92.4"),
    _holding("NVDA", "US", "USD", "150", "142.3"),
    _holding("MSFT", "US", "USD", "40", "455.8"),
    _holding("CASH", None, "TWD", "600000", "1"),
]
# The largest holding is 30, the smallest held one 10, and the US holdings add up to 30.
TARGETS = {"2330.TW": 30, "0050.TW": 30, "NVDA": 20, "MSFT": 10, "CASH": 10}


def _rule(kind: RuleKind, limit: int, market: Market | None = None) -> RuleView:
    return RuleView(kind=kind, limit_percent=limit, market=market, enabled=True)


@pytest.mark.parametrize(
    ("rule", "met", "measured", "breaking"),
    [
        pytest.param(_rule("max_holding_weight", 30), True, 30, [], id="max at limit"),
        pytest.param(
            _rule("max_holding_weight", 29),
            False,
            30,
            ["2330.TW", "0050.TW"],
            id="max one below",
        ),
        pytest.param(_rule("min_holding_weight", 10), True, 10, [], id="min at limit"),
        pytest.param(
            _rule("min_holding_weight", 11), False, 10, ["MSFT"], id="min one above"
        ),
        pytest.param(
            _rule("max_market_weight", 30, "US"), True, 30, [], id="market at limit"
        ),
        pytest.param(
            _rule("max_market_weight", 29, "US"),
            False,
            30,
            ["NVDA", "MSFT"],
            id="market one below",
        ),
        pytest.param(
            _rule("max_market_weight", 60, "TW"), True, 60, [], id="the other market"
        ),
    ],
)
def test_each_kind_is_met_at_its_limit_and_broken_one_past_it(
    rule: RuleView, met: bool, measured: int, breaking: list[str]
) -> None:
    checks = rule_checks([rule], HOLDINGS, TARGETS)

    check = checks.rules[0]
    assert (check.met, check.measured, check.breaking) == (met, measured, breaking)
    assert (checks.met, checks.enabled) == (int(met), 1)


def test_cash_is_not_a_holding_the_rules_look_at() -> None:
    targets = {"2330.TW": 15, "0050.TW": 15, "NVDA": 15, "MSFT": 15, "CASH": 40}

    checks = rule_checks([_rule("max_holding_weight", 30)], HOLDINGS, targets)

    assert checks.rules[0].met is True
    assert checks.rules[0].measured == 15


def test_a_holding_the_strategy_holds_none_of_is_not_under_the_least_weight() -> None:
    targets = {"2330.TW": 40, "0050.TW": 30, "NVDA": 20, "MSFT": 0, "CASH": 10}

    checks = rule_checks([_rule("min_holding_weight", 10)], HOLDINGS, targets)

    assert checks.rules[0].met is True
    assert checks.rules[0].measured == 20


def test_a_rule_that_is_off_has_no_result_and_is_not_counted() -> None:
    off = RuleView(
        kind="max_holding_weight", limit_percent=5, market=None, enabled=False
    )

    checks = rule_checks([off, _rule("min_holding_weight", 10)], HOLDINGS, TARGETS)

    assert (checks.met, checks.enabled) == (1, 1)
    assert (checks.rules[0].met, checks.rules[0].measured) == (None, None)
    assert checks.rules[0].breaking == []


def test_every_kind_has_a_measure_and_a_market_entry() -> None:
    assert set(RULE_MEASURES) == set(get_args(RuleKind))
    assert set(store.NAMES_A_MARKET) == set(get_args(RuleKind))


def _input(**changes: Any) -> RuleInput:
    fields: dict[str, Any] = {
        "kind": "max_holding_weight",
        "limit_percent": 30,
        "market": None,
        "enabled": True,
    }
    return RuleInput.model_validate(fields | changes)


@pytest.mark.parametrize(
    ("rule", "code"),
    [
        pytest.param(_input(kind="max_cash_weight"), "rule_unknown_kind", id="kind"),
        pytest.param(_input(limit_percent=-1), "rule_limit_out_of_range", id="-1"),
        pytest.param(_input(limit_percent=101), "rule_limit_out_of_range", id="101"),
        pytest.param(
            _input(kind="max_market_weight", market=None), "rule_market", id="no market"
        ),
        pytest.param(
            _input(kind="max_market_weight", market="JP"),
            "rule_market",
            id="unknown market",
        ),
        pytest.param(_input(market="US"), "rule_market", id="a market it does not use"),
    ],
)
def test_a_rule_the_service_cannot_check_is_refused_with_its_code_and_place(
    rule: RuleInput, code: StrategyErrorCode
) -> None:
    with pytest.raises(store.RuleRefusedError) as refused:
        store.check_rules([_input(), rule])

    assert refused.value.code == code
    assert str(refused.value).startswith("rule 2:")


def test_rules_at_the_edges_of_the_limits_are_kept_in_order() -> None:
    rules = [
        _input(limit_percent=0),
        _input(kind="max_market_weight", limit_percent=100, market="US"),
        _input(kind="min_holding_weight", limit_percent=5, enabled=False),
    ]

    kept = store.check_rules(rules)

    assert [(rule.kind, rule.limit_percent) for rule in kept] == [
        ("max_holding_weight", 0),
        ("max_market_weight", 100),
        ("min_holding_weight", 5),
    ]
