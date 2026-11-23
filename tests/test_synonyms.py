"""The synonym table: its format checks and how a question is expanded."""

from pathlib import Path

import pytest

from chat_bridge.synonyms import (
    MAX_SYNONYMS_PER_GROUP,
    SynonymFileError,
    load_synonyms,
)


def write(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "synonyms.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def test_the_project_synonym_file_passes_its_own_checks() -> None:
    assert load_synonyms().groups


def test_every_problem_is_reported_at_once_with_its_line(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "# a comment",
        "",
        "央行, 中央銀行",
        "歐洲央行, ECB",
        "i-pod, i pod => ipod",
        "solo",
        "a, , b",
        "Fed, Federal Reserve",
        "FED, 聯準會",
    )

    with pytest.raises(SynonymFileError) as raised:
        load_synonyms(path)

    message = str(raised.value)
    expected = [
        "line 5: '=>' mappings are not supported",
        "line 6: a group needs at least two names",
        "line 7: a name is empty",
        "line 9: 'FED' is already on line 8",
        "line 3: '央行' is inside '歐洲央行' on line 4",
    ]
    assert all(problem in message for problem in expected), message


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("台達", ["台達電", "台達電子", "Delta Electronics"]),
        ("大摩", ["摩根士丹利", "Morgan Stanley"]),
        # Intel is a whole English word, so "intelligence" does not mention it.
        ("intelligence report", []),
    ],
)
def test_a_question_searches_for_the_other_names_of_its_groups(
    question: str, expected: list[str]
) -> None:
    assert load_synonyms().expand(question) == expected


def test_one_group_adds_a_limited_number_of_names(tmp_path: Path) -> None:
    names = [f"name{number}" for number in range(MAX_SYNONYMS_PER_GROUP + 3)]
    path = write(tmp_path, ", ".join(names))

    expanded = load_synonyms(path).expand("name0")

    assert expanded == names[1 : MAX_SYNONYMS_PER_GROUP + 1]
