"""Reading a file into Markdown or pages, and the reasons a file is refused."""

import codecs
import io
import zipfile
from pathlib import Path

import pytest
from pypdf import PdfWriter

from chat_bridge.config import PROJECT_ROOT
from chat_bridge.ingest.readers import (
    RejectReason,
    UnreadableFileError,
    is_supported,
    read_markdown,
)
from chat_bridge.ingest.sections import read_document, split_tables

# The real long documents shipped with the demo. The central bank file (124 pages) is read in
# the slow tests only.
SAMPLE_DOCUMENTS = PROJECT_ROOT / "data" / "documents"
ETF_QA = SAMPLE_DOCUMENTS / "sfb-etf-qa-2003.pdf"
MODEL_CLAUSES = SAMPLE_DOCUMENTS / "fsc-life-insurance-model-clauses-2006.doc"

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


def blank_pdf() -> bytes:
    """A one-page PDF with no text, as a scan without a text layer reads."""
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


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
        pytest.param(
            "clauses.odt", b"PK", RejectReason.OPENDOCUMENT, id="OpenDocument text"
        ),
        pytest.param(
            "broken.pdf", b"not a pdf", RejectReason.CONVERSION_FAILED, id="broken PDF"
        ),
        pytest.param(
            "broken.doc",
            b"not a doc",
            RejectReason.CONVERSION_FAILED,
            id="broken Word 97",
        ),
        pytest.param(
            "scan.pdf", blank_pdf(), RejectReason.NO_TEXT, id="PDF without text"
        ),
    ],
)
def test_a_file_without_usable_text_is_refused_with_the_reason(
    tmp_path: Path, name: str, data: bytes, reason: RejectReason
) -> None:
    with pytest.raises(UnreadableFileError) as raised:
        read_document(write_bytes(tmp_path, name, data))

    assert raised.value.reason == reason


def test_the_extension_is_matched_without_case() -> None:
    assert is_supported(Path("REPORT.DOCX"))
    assert is_supported(Path("CLAUSES.DOC"))
    assert is_supported(Path("GUIDELINES.PDF"))
    assert not is_supported(Path("report.xlsx"))
    assert not is_supported(Path("clauses.odt"))


def test_the_refusal_of_opendocument_says_what_to_do(tmp_path: Path) -> None:
    with pytest.raises(UnreadableFileError) as raised:
        read_document(write_bytes(tmp_path, "clauses.odt", b"PK"))

    assert "save it as .docx or PDF" in str(raised.value)


@pytest.mark.parametrize(
    "name",
    ["fsc-ai-guidelines-2024.pdf", "sfb-article-70-1-qa.pdf", "sfb-etf-qa-2003.pdf"],
)
def test_a_sample_pdf_becomes_one_section_per_page(name: str) -> None:
    document = read_document(SAMPLE_DOCUMENTS / name)

    assert len(document.sections) > 1
    assert all(section.heading.startswith("Page ") for section in document.sections)
    assert document.title == Path(name).stem


def test_the_etf_qa_first_question_is_on_its_first_page() -> None:
    first = read_document(ETF_QA).sections[0]

    assert first.heading == "Page 1"
    assert "何謂指數股票型基金？投資人如何買賣指數股票型基金？" in first.content


def test_a_word_97_file_is_read_with_its_title_and_tables() -> None:
    parts = split_tables(read_markdown(MODEL_CLAUSES))

    assert parts.text.startswith("# 人壽保險單示範條款修正條文對照表")
    assert any("要保人於保險單送達的翌日起算十日內" in table for table in parts.tables)


def test_a_word_table_becomes_a_markdown_table(tmp_path: Path) -> None:
    path = tmp_path / "report.docx"
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in DOCX_PARTS.items():
            archive.writestr(name, content)

    parts = split_tables(read_markdown(path))

    assert "台達電 fell after the report." in parts.text
    assert len(parts.tables) == 1
    assert "1270" in parts.tables[0]
