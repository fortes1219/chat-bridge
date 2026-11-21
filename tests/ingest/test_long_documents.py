"""Real long documents: the sample PDFs and Word 97 file are cut into passages that are found.

This needs the embedding model and the embedded database, and the central bank file has 124
pages, so it is marked slow.
"""

import asyncio
import shutil
from collections.abc import Iterator

import pytest

from chat_bridge.config import PROJECT_ROOT
from chat_bridge.embedding import PASSAGE_TOKEN_LIMIT, load_model
from chat_bridge.ingest.readers import RejectReason
from chat_bridge.ingest.service import IngestReport
from chat_bridge.search.service import search
from tests.utils import ingest, prepare_local_data, run_sql, using_local_data

pytestmark = pytest.mark.slow

SAMPLE_DOCUMENTS = PROJECT_ROOT / "data" / "documents"
PDFS = sorted(path.name for path in SAMPLE_DOCUMENTS.glob("*.pdf"))
ODT_NAME = "clauses-2018.odt"
# The spec's searches: the question, the file that answers it, and words of the answer.
SEARCHES = [
    pytest.param(
        "何謂指數股票型基金？投資人如何買賣指數股票型基金？",
        "sfb-etf-qa-2003.pdf",
        "在證券交易所上市買賣",
        id="ETF Q&A",
    ),
    pytest.param(
        "本法第70條之1規範之對象包括哪些?",
        "sfb-article-70-1-qa.pdf",
        "網際網路平臺提供者",
        id="Article 70-1 Q&A",
    ),
    pytest.param(
        "落實透明性與可解釋性",
        "fsc-ai-guidelines-2024.pdf",
        "可解釋性",
        id="AI guidelines",
    ),
    pytest.param(
        "第2戶購屋貸款成數",
        "cbc-board-meeting-reference-2026-09-17.pdf",
        "購屋貸款成數上限至6成",
        id="central bank",
    ),
    pytest.param(
        "要保人於保險單送達的翌日起算十日內",
        "fsc-life-insurance-model-clauses-2006.doc",
        "要保人於保險單送達的翌日起算十日內",
        id="Word 97 clause",
    ),
]
FIRST = 8
# A table of contents lists chapter titles with dot leaders; a hit there is not the chapter.
CONTENTS_LEADER = "....."
# A PDF's text keeps a space where a line broke, so answers are compared without spaces.
SPACE = " "


@pytest.fixture(scope="module")
def long_documents(tmp_path_factory: pytest.TempPathFactory) -> Iterator[IngestReport]:
    folder = tmp_path_factory.mktemp("documents")
    for path in SAMPLE_DOCUMENTS.iterdir():
        shutil.copyfile(path, folder / path.name)
    (folder / ODT_NAME).write_bytes(b"PK")
    local_data = prepare_local_data(tmp_path_factory.mktemp("long_local_data"))
    with using_local_data(local_data):
        yield ingest(folder)


def test_every_readable_file_is_ingested_and_the_odt_is_refused(
    long_documents: IngestReport,
) -> None:
    assert len(long_documents.written) == len(PDFS) + 1
    assert [(r.source_path, r.reason) for r in long_documents.rejected] == [
        (ODT_NAME, RejectReason.OPENDOCUMENT)
    ]


def test_each_pdf_is_cut_into_passages_within_the_limit(
    long_documents: IngestReport,
) -> None:
    rows = run_sql(
        "SELECT d.source_path, s.heading, e.content FROM search_entries e "
        "JOIN sections s ON s.id = e.section_id JOIN documents d ON d.id = s.document_id "
        "WHERE e.source = 'section'"
    )
    tokenizer = load_model().tokenizer
    for name in PDFS:
        assert sum(1 for row in rows if row.source_path == name) > 1, name
    for row in rows:
        # An entry is the heading path, a line break, then the passage text.
        text = row.content[len(row.heading) + 1 :] if row.heading else row.content
        assert len(tokenizer.tokenize(text)) <= PASSAGE_TOKEN_LIMIT, row.source_path


@pytest.mark.parametrize(("question", "source_path", "answer"), SEARCHES)
def test_a_search_finds_the_passage_that_answers(
    long_documents: IngestReport, question: str, source_path: str, answer: str
) -> None:
    hits = asyncio.run(search(question, FIRST)).hits

    assert any(
        hit.source_path == source_path
        and answer in hit.content.replace(SPACE, "")
        and CONTENTS_LEADER not in hit.content
        for hit in hits
    ), [(hit.source_path, hit.heading) for hit in hits]


@pytest.mark.parametrize(
    ("question", "source_path"),
    [
        ("何謂指數股票型基金？投資人如何買賣指數股票型基金？", "sfb-etf-qa-2003.pdf"),
        ("落實透明性與可解釋性", "fsc-ai-guidelines-2024.pdf"),
    ],
)
def test_a_found_passage_shows_the_page_it_is_on(
    long_documents: IngestReport, question: str, source_path: str
) -> None:
    hits = asyncio.run(search(question, FIRST)).hits

    assert any(
        hit.source_path == source_path and hit.heading.startswith("Page ")
        for hit in hits
    )


def test_every_section_of_a_pdf_is_a_page(long_documents: IngestReport) -> None:
    # A PDF's text is not parsed as Markdown, so no line of it becomes a heading.
    rows = run_sql(
        "SELECT d.source_path, s.heading FROM sections s "
        "JOIN documents d ON d.id = s.document_id WHERE d.source_path LIKE '%.pdf'"
    )

    assert rows
    assert all(row.heading.startswith("Page ") for row in rows), {
        row.heading for row in rows if not row.heading.startswith("Page ")
    }
