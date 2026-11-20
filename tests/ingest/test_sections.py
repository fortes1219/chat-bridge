"""Splitting Markdown into sections, and taking tables out of a section."""

import pytest

from chat_bridge.ingest.readers import RejectReason, UnreadableFileError
from chat_bridge.ingest.sections import SectionParts, parse_markdown, split_tables

TABLE = "| name | close |\n|---|---|\n| 台達電 | 1270 |"
OTHER_TABLE = "| index | change |\n|---|---|\n| SOX | -3.20% |"

# ------------------------------------------------------------------ Tables


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(
            "Plain text only.", SectionParts("Plain text only.", []), id="text only"
        ),
        pytest.param(TABLE, SectionParts("", [TABLE]), id="table only"),
        pytest.param(
            f"Before the table.\n\n{TABLE}\n\nAfter the table.",
            SectionParts("Before the table.\n\n\nAfter the table.", [TABLE]),
            id="text around a table",
        ),
        pytest.param(
            f"{TABLE}\n\nBetween.\n\n{OTHER_TABLE}",
            SectionParts("Between.", [TABLE, OTHER_TABLE]),
            id="two tables",
        ),
        pytest.param(
            f"```\n{TABLE}\n```",
            SectionParts(f"```\n{TABLE}\n```", []),
            id="table in a code block",
        ),
        pytest.param(
            "a | b | c\nno delimiter row here",
            SectionParts("a | b | c\nno delimiter row here", []),
            id="pipes without a table",
        ),
    ],
)
def test_tables_are_taken_out_of_the_text(content: str, expected: SectionParts) -> None:
    assert split_tables(content) == expected


# ---------------------------------------------------------------- Sections


def test_sections_keep_the_path_of_headings_above_them() -> None:
    document = parse_markdown(
        "Before any heading.\n\n# Event\n\nWhat happened.\n\n## Evidence\n\nThe numbers.\n",
        fallback_title="file",
    )

    assert [(s.heading, s.content) for s in document.sections] == [
        ("", "Before any heading."),
        ("Event", "What happened."),
        ("Event > Evidence", "The numbers."),
    ]


def test_a_heading_inside_a_code_block_does_not_start_a_section() -> None:
    document = parse_markdown(
        "# Real\n\n```\n# not a heading\n```\n", fallback_title="file"
    )

    assert [s.heading for s in document.sections] == ["Real"]


def test_front_matter_gives_the_title_and_keyword_groups() -> None:
    document = parse_markdown(
        "---\ntitle: From front matter\nkeyword_groups:\n  - [費半, SOX]\n---\n# Heading\n\nBody.\n",
        fallback_title="file",
    )

    assert document.title == "From front matter"
    assert document.keyword_groups == [["費半", "SOX"]]


@pytest.mark.parametrize(
    ("text", "title"),
    [
        pytest.param("# First heading\n\nBody.\n", "First heading", id="first heading"),
        pytest.param("Only body text.\n", "file", id="file name"),
    ],
)
def test_without_a_front_matter_title_the_title_falls_back(
    text: str, title: str
) -> None:
    assert parse_markdown(text, fallback_title="file").title == title


@pytest.mark.parametrize(
    "front_matter",
    [
        pytest.param("title: [unclosed", id="broken YAML"),
        pytest.param("keyword_groups: not a list", id="wrong type"),
    ],
)
def test_invalid_front_matter_is_refused(front_matter: str) -> None:
    with pytest.raises(UnreadableFileError) as raised:
        parse_markdown(f"---\n{front_matter}\n---\nBody.\n", fallback_title="file")

    assert raised.value.reason == RejectReason.INVALID_FRONT_MATTER
