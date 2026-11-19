"""Ingest a folder: read, split, tokenize, and store, skipping files whose bytes have not changed.

The shape follows private-gpt's `make ingest <folder>`: walk the folder, pick a reader by
extension, convert to Markdown, split at headings, and skip a file whose SHA-256 is unchanged.
All writes of one run happen in one transaction, so a failure leaves nothing half-written.
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chat_bridge.database import create_tables, open_engine
from chat_bridge.ingest.models import (
    LEAD_SECTION_POSITION,
    Document,
    EntrySource,
    SearchEntry,
    Section,
    TokenizerState,
)
from chat_bridge.ingest.readers import (
    RejectReason,
    UnreadableFileError,
    is_supported,
    read_markdown,
)
from chat_bridge.ingest.sections import ParsedDocument, parse_markdown
from chat_bridge.tokenizer import (
    DICTIONARY_BLOB_SHA1,
    SearchTokenizer,
    build_tokenizer,
    ensure_dictionary,
    index_text,
)

# private-gpt hashes files in 4 KB chunks.
HASH_CHUNK_BYTES = 4096
TOKENIZER_STATE_ID = 1

INSERT_ENTRY = text(
    "INSERT INTO search_entries (section_id, source, search_vector) "
    "VALUES (:section_id, :source, to_tsvector('simple', :words))"
)


@dataclass(frozen=True)
class Rejection:
    source_path: str
    reason: RejectReason
    detail: str


@dataclass
class IngestReport:
    written: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)
    # Files that were stored before but are now rejected. Their old version is removed.
    removed: list[str] = field(default_factory=list)
    sections_written: int = 0
    reindexed_all: bool = False


@dataclass(frozen=True)
class _Candidate:
    source_path: str
    path: Path
    content_hash: str


@dataclass(frozen=True)
class _Prepared:
    candidate: _Candidate
    document: ParsedDocument


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def section_text(heading: str, content: str) -> str:
    """The text a section is found by: its heading path and its content."""
    return f"{heading}\n{content}" if heading else content


def keyword_text(keyword_groups: list[list[str]]) -> str:
    """Every name in a document's keyword groups, one per line."""
    return "\n".join(name for group in keyword_groups for name in group)


async def stored_user_words(session: AsyncSession) -> list[str]:
    """Every name in every stored document's keyword groups. They become jieba user words,
    as MaxKB loads its term base on each save and each search."""
    groups = (await session.scalars(select(Document.keyword_groups))).all()
    return [
        name
        for document_groups in groups
        for group in document_groups
        for name in group
    ]


def _walk(root: Path) -> list[Path]:
    # rglob walks the tree without recursion in our code. Sorting keeps the order the same on
    # every run, as docling's command line does.
    return sorted(path for path in root.rglob("*") if path.is_file())


def _collect(root: Path, report: IngestReport) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for path in _walk(root):
        source_path = path.relative_to(root).as_posix()
        if not is_supported(path):
            detail = path.suffix or "(no extension)"
            report.rejected.append(
                Rejection(source_path, RejectReason.UNSUPPORTED_TYPE, detail)
            )
            continue
        candidates.append(_Candidate(source_path, path, file_sha256(path)))
    return candidates


def _prepare(changed: Sequence[_Candidate], report: IngestReport) -> list[_Prepared]:
    prepared: list[_Prepared] = []
    for candidate in changed:
        try:
            document = parse_markdown(
                read_markdown(candidate.path), fallback_title=candidate.path.stem
            )
        except UnreadableFileError as error:
            report.rejected.append(
                Rejection(candidate.source_path, error.reason, error.detail)
            )
            continue
        prepared.append(_Prepared(candidate, document))
    return prepared


async def _insert(session: AsyncSession, item: _Prepared, report: IngestReport) -> int:
    document = Document(
        source_path=item.candidate.source_path,
        content_hash=item.candidate.content_hash,
        title=item.document.title,
        keyword_groups=item.document.keyword_groups,
    )
    session.add(document)
    await session.flush()
    session.add_all(
        Section(
            document_id=document.id,
            position=section.position,
            heading=section.heading,
            content=section.content,
        )
        for section in item.document.sections
    )
    report.written.append(item.candidate.source_path)
    report.sections_written += len(item.document.sections)
    return document.id


async def _index_sections(
    session: AsyncSession,
    tokenizer: SearchTokenizer,
    document_ids: Sequence[int] | None,
) -> None:
    """Write the search entries of the given documents. None means every document, and the
    old entries are deleted first. New documents have no entries yet."""
    query = select(
        Section.id,
        Section.position,
        Section.heading,
        Section.content,
        Document.keyword_groups,
    ).join(Document, Section.document_id == Document.id)
    if document_ids is None:
        await session.execute(delete(SearchEntry))
    else:
        query = query.where(Section.document_id.in_(document_ids))

    entries: list[dict[str, object]] = []
    for row in (await session.execute(query)).all():
        words = index_text(tokenizer, section_text(row.heading, row.content))
        entries.append(
            {"section_id": row.id, "source": EntrySource.SECTION, "words": words}
        )
        if row.position == LEAD_SECTION_POSITION and row.keyword_groups:
            words = index_text(tokenizer, keyword_text(row.keyword_groups))
            entries.append(
                {"section_id": row.id, "source": EntrySource.KEYWORDS, "words": words}
            )
    if entries:
        await session.execute(INSERT_ENTRY, entries)


async def _store(
    session: AsyncSession,
    prepared: Sequence[_Prepared],
    stale_paths: Sequence[str],
    report: IngestReport,
) -> None:
    state = await session.get(TokenizerState, TOKENIZER_STATE_ID)
    dictionary_changed = state is None or state.dictionary_sha1 != DICTIONARY_BLOB_SHA1
    replaced_paths = [item.candidate.source_path for item in prepared] + list(
        stale_paths
    )
    if not replaced_paths and not dictionary_changed:
        return

    if replaced_paths:
        await session.execute(
            delete(Document).where(Document.source_path.in_(replaced_paths))
        )
    new_document_ids = [await _insert(session, item, report) for item in prepared]

    tokenizer = build_tokenizer(await stored_user_words(session))
    # New user words change how every section is cut, so the whole index is rebuilt.
    reindex_all = (
        state is None
        or dictionary_changed
        or state.user_words_digest != tokenizer.user_words_digest
    )
    report.reindexed_all = reindex_all
    await _index_sections(session, tokenizer, None if reindex_all else new_document_ids)

    if state is None:
        session.add(
            TokenizerState(
                id=TOKENIZER_STATE_ID,
                dictionary_sha1=DICTIONARY_BLOB_SHA1,
                user_words_digest=tokenizer.user_words_digest,
            )
        )
    else:
        state.dictionary_sha1 = DICTIONARY_BLOB_SHA1
        state.user_words_digest = tokenizer.user_words_digest


async def ingest_folder(root: Path) -> IngestReport:
    """Ingest every supported file under `root`. Paths are stored relative to `root`."""
    report = IngestReport()
    candidates = _collect(root, report)
    # Download the dictionary before the transaction opens, so no network call runs inside it.
    ensure_dictionary()

    async with open_engine() as engine:
        await create_tables(engine)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            paths = [candidate.source_path for candidate in candidates]
            rows = await session.execute(
                select(Document.source_path, Document.content_hash).where(
                    Document.source_path.in_(paths)
                )
            )
            stored = {row.source_path: row.content_hash for row in rows}

        changed: list[_Candidate] = []
        for candidate in candidates:
            if stored.get(candidate.source_path) == candidate.content_hash:
                report.unchanged.append(candidate.source_path)
                continue
            changed.append(candidate)

        prepared = _prepare(changed, report)
        prepared_paths = {item.candidate.source_path for item in prepared}
        stale_paths = [
            c.source_path
            for c in changed
            if c.source_path in stored and c.source_path not in prepared_paths
        ]
        report.removed.extend(stale_paths)

        async with sessions() as session, session.begin():
            await _store(session, prepared, stale_paths, report)
    return report
