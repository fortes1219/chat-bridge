"""Reading a file as Markdown, and the reasons a file is refused."""

import codecs
import zipfile
from pathlib import Path

import pytest

from chat_bridge.ingest.readers import (
    RejectReason,
    UnreadableFileError,
    is_supported,
    read_markdown,
)
from chat_bridge.ingest.sections import split_tables

# The smallest Word file: the content types, the package relationship, and the document.
DOCX_PARTS = {
    "[Content_Types].xml": (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    ),
    "_rels/.rels": (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
        '2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    ),
    "word/document.xml": (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>台達電 fell after the report.</w:t></w:r></w:p>"
        "<w:tbl>"
        "<w:tr><w:tc><w:p><w:r><w:t>Name</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>Close</w:t></w:r></w:p></w:tc></w:tr>"
        "<w:tr><w:tc><w:p><w:r><w:t>台達電</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>1270</w:t></w:r></w:p></w:tc></w:tr>"
        "</w:tbl>"
        "</w:body></w:document>"
    ),
}


def write_bytes(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


@pytest.mark.parametrize(
    ("name", "data"),
    [
        pytest.param("note.md", "台積電法說會".encode(), id="UTF-8"),
        pytest.param(
            "note.txt", codecs.BOM_UTF8 + "台積電法說會".encode(), id="UTF-8 with BOM"
        ),
        pytest.param("note.txt", "台積電法說會".encode("utf-16"), id="UTF-16 with BOM"),
    ],
)
def test_text_files_are_read_as_written(tmp_path: Path, name: str, data: bytes) -> None:
    assert read_markdown(write_bytes(tmp_path, name, data)) == "台積電法說會"


@pytest.mark.parametrize(
    ("name", "data", "reason"),
    [
        pytest.param(
            "big5.txt", "台積電".encode("big5"), RejectReason.NOT_UTF8, id="not UTF-8"
        ),
        pytest.param("nul.txt", b"text\x00more", RejectReason.BINARY, id="binary"),
        pytest.param("blank.md", b"  \n\t\n", RejectReason.NO_TEXT, id="no text"),
        pytest.param(
            "sheet.xlsx", b"PK", RejectReason.UNSUPPORTED_TYPE, id="unsupported type"
        ),
    ],
)
def test_a_file_without_usable_text_is_refused_with_the_reason(
    tmp_path: Path, name: str, data: bytes, reason: RejectReason
) -> None:
    with pytest.raises(UnreadableFileError) as raised:
        read_markdown(write_bytes(tmp_path, name, data))

    assert raised.value.reason == reason


def test_the_extension_is_matched_without_case() -> None:
    assert is_supported(Path("REPORT.DOCX"))
    assert not is_supported(Path("report.xlsx"))


def test_a_word_table_becomes_a_markdown_table(tmp_path: Path) -> None:
    path = tmp_path / "report.docx"
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in DOCX_PARTS.items():
            archive.writestr(name, content)

    parts = split_tables(read_markdown(path))

    assert "台達電 fell after the report." in parts.text
    assert len(parts.tables) == 1
    assert "1270" in parts.tables[0]
