"""The rules read from the docs that describe a truth file."""

import pytest

from chat_bridge.collect.record import record_schema
from chat_bridge.collect.rules import FORMAT_FILE, RulesError, read_rules, rules_from

MARKETS = ("US", "TW")


def test_the_docs_give_the_targets_sections_values_and_words() -> None:
    rules = read_rules()

    assert sorted(rules.targets) == [1, 2, 3, 4, 5]
    assert rules.targets[5] == "這波下跌是否有權威說法指出股市回到正常趨勢。"
    assert rules.headings == ("事件發生", "影響股市證據", "相關標的", "後續與不同說法")
    assert rules.optional == frozenset({"後續與不同說法"})
    assert rules.significance == ("key", "supporting", "background")
    assert len(rules.exposure) == 20 and "ai_debt_credit" in rules.exposure
    assert set(rules.markets) == {"US", "TW"}


def test_the_record_schema_holds_the_agent_to_the_rules() -> None:
    schema = record_schema(read_rules(), ["s1", "s2"], [])
    properties = schema["properties"]

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(properties)
    assert properties["targets"]["items"]["enum"] == [1, 2, 3, 4, 5]
    assert len(properties["exposure"]["items"]["enum"]) == 20
    section = properties["sections"]["items"]["properties"]
    assert section["heading"]["enum"][0] == "事件發生"
    assert section["items"]["items"]["properties"]["source"]["enum"] == ["s1", "s2"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda text: text.replace("| `tickers` |", "| `ticker_list` |"),
            "ticker_list",
        ),
        (
            lambda text: text.replace("採集目標（`targets`）：", "採集目標："),
            "collection targets",
        ),
        (lambda text: text.replace("`## 事件發生`", "事件發生"), "the sections"),
    ],
    ids=["another key", "no targets", "no headings"],
)
def test_a_format_the_program_cannot_follow_stops_it(
    change: object, message: str
) -> None:
    text = FORMAT_FILE.read_text(encoding="utf-8")
    vocabulary = read_rules().vocabulary_text

    with pytest.raises(RulesError, match=message):
        rules_from(change(text), vocabulary, MARKETS)  # type: ignore[operator]


def test_a_vocabulary_with_no_words_stops_it() -> None:
    text = FORMAT_FILE.read_text(encoding="utf-8")

    with pytest.raises(RulesError, match="exposure words"):
        rules_from(text, "# exposure 詞表\n\nNo list here.\n", MARKETS)
