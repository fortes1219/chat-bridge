"""Ingest a folder: read, split, tokenize, embed, and store, skipping unchanged files.

The shape follows private-gpt's `make ingest <folder>`: walk the folder, pick a reader by
extension, convert to Markdown, split at headings, and skip a file whose SHA-256 is unchanged.
All writes of one run happen in one transaction, so a failure leaves nothing half-written.
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chat_bridge.database import create_tables, open_engine, vacuum
from chat_bridge.embedding import (
    MODEL_NAME,
    MODEL_REVISION,
    embed_documents,
    load_model,
    split_for_model,
)
from chat_bridge.ingest.models import (
    ENTRY_LAYOUT,
    LEAD_SECTION_POSITION,
    SOURCE_RULES,
    Document,
    EmbeddingState,
    EntryLayoutState,
    EntrySource,
    SearchEntry,
    Section,
    TokenizerState,
)
from chat_bridge.ingest.readers import (
    RejectReason,
    UnreadableFileError,
    is_supported,
    unsupported_reason,
)
from chat_bridge.ingest.sections import ParsedDocument, read_document, split_tables
from chat_bridge.synonyms import Synonyms, load_synonyms
from chat_bridge.tokenizer import (
    DICTIONARY_BLOB_SHA1,
    SearchTokenizer,
    build_tokenizer,
    ensure_dictionary,
    index_text,
    user_words_digest,
)

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

# private-gpt hashes files in 4 KB chunks.
HASH_CHUNK_BYTES = 4096
TOKENIZER_STATE_ID = 1
EMBEDDING_STATE_ID = 1
ENTRY_LAYOUT_STATE_ID = 1

# setweight labels every word with its source's weight (SOURCE_RULES), as the PostgreSQL
# manual uses setweight to mark entries that come from different parts of a document. The
# label is sent as text: asyncpg encodes a "char" parameter as bytes.
WEIGHTED_WORDS = (
    "setweight(to_tsvector('simple', :words), CAST(CAST(:weight AS text) AS \"char\"))"
)
INSERT_ENTRY = text(
    "INSERT INTO search_entries (section_id, source, content, search_vector, embedding_bge_m3) "
    f"VALUES (:section_id, :source, :content, {WEIGHTED_WORDS}, :embedding)"
)
UPDATE_ENTRY_WORDS = text(
    f"UPDATE search_entries SET search_vector = {WEIGHTED_WORDS} WHERE id = :id"
)


class IndexUpdate(StrEnum):
    """What a run did to the search entries."""

    NONE = "none"
    WRITTEN_FILES = "written_files"  # entries added for the written files only
    KEYWORDS = "keywords"  # the tokenizer changed: every entry's words rebuilt, embeddings kept
    ALL = "all"  # the model or the entry layout changed: every entry rebuilt and embedded again


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
    index_update: IndexUpdate = IndexUpdate.NONE


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


async def user_words(session: AsyncSession, synonyms: Synonyms) -> list[str]:
    """The jieba user words: every name in the stored documents' keyword groups and in the
    synonym table, as MaxKB loads its term base on each save and each search."""
    groups = (await session.scalars(select(Document.keyword_groups))).all()
    keyword_names = [
        name
        for document_groups in groups
        for group in document_groups
        for name in group
    ]
    return keyword_names + synonyms.names()


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
                Rejection(source_path, unsupported_reason(path), detail)
            )
            continue
        candidates.append(_Candidate(source_path, path, file_sha256(path)))
    return candidates


def _prepare(changed: Sequence[_Candidate], report: IngestReport) -> list[_Prepared]:
    prepared: list[_Prepared] = []
    for candidate in changed:
        try:
            document = read_document(candidate.path)
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
        event_date=item.document.event_date,
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


async def _add_entries(
    session: AsyncSession,
    tokenizer: SearchTokenizer,
    model: "SentenceTransformer",
    document_ids: Sequence[int] | None,
) -> None:
    """Write the search entries of the given documents' sections. None means every document.

    The text of an entry goes to the model as it is, as RAGFlow sends the original text.
    Only sources that SOURCE_RULES marks as embedded are embedded, all in one batched call. An
    embedded text longer than a passage is split into passages first, and each passage carries
    the section's heading path, so a piece from the middle of a section is still found by its
    heading. A text that is not embedded, such as a table, is never split.
    """
    query = select(
        Section.id,
        Section.position,
        Section.heading,
        Section.content,
        Document.keyword_groups,
    ).join(Document, Section.document_id == Document.id)
    if document_ids is not None:
        query = query.where(Section.document_id.in_(document_ids))

    # Each text with the heading path it is found by; the keyword list has none.
    texts: list[tuple[int, EntrySource, str, str]] = []
    for row in (await session.execute(query)).all():
        content = split_tables(row.content)
        if content.text:
            texts.append((row.id, EntrySource.SECTION, row.heading, content.text))
        texts.extend(
            (row.id, EntrySource.TABLE, row.heading, table) for table in content.tables
        )
        if row.position == LEAD_SECTION_POSITION and row.keyword_groups:
            texts.append(
                (row.id, EntrySource.KEYWORDS, "", keyword_text(row.keyword_groups))
            )

    parts = [
        (section_id, source, section_text(heading, piece))
        for section_id, source, heading, text in texts
        for piece in (
            split_for_model(model, text) if SOURCE_RULES[source].embedded else [text]
        )
    ]
    if not parts:
        return
    embedded = [
        index
        for index, (_, source, _) in enumerate(parts)
        if SOURCE_RULES[source].embedded
    ]
    vectors = embed_documents(model, [parts[index][2] for index in embedded])
    embedding_of = dict(zip(embedded, vectors, strict=True))
    entries = [
        {
            "section_id": section_id,
            "source": source,
            "content": part,
            "words": index_text(tokenizer, part),
            "weight": SOURCE_RULES[source].weight,
            "embedding": embedding_of[index] if SOURCE_RULES[source].embedded else None,
        }
        for index, (section_id, source, part) in enumerate(parts)
    ]
    await session.execute(INSERT_ENTRY, entries)


async def _rebuild_words(session: AsyncSession, tokenizer: SearchTokenizer) -> None:
    """Rebuild every stored entry's words from its own text. The embeddings stay as they are."""
    rows = (
        await session.execute(
            select(SearchEntry.id, SearchEntry.source, SearchEntry.content)
        )
    ).all()
    if not rows:
        return
    await session.execute(
        UPDATE_ENTRY_WORDS,
        [
            {
                "id": row.id,
                "words": index_text(tokenizer, row.content),
                "weight": SOURCE_RULES[EntrySource(row.source)].weight,
            }
            for row in rows
        ],
    )


def _entries_are_current(
    embedding_state: EmbeddingState | None, layout_state: EntryLayoutState | None
) -> bool:
    """Whether the stored entries were cut with this layout and embedded with this model."""
    return (
        embedding_state is not None
        and layout_state is not None
        and (
            embedding_state.model_name,
            embedding_state.model_revision,
            layout_state.layout,
        )
        == (MODEL_NAME, MODEL_REVISION, ENTRY_LAYOUT)
    )


def _words_are_current(state: TokenizerState | None, words_digest: str) -> bool:
    """Whether the stored words were built with this dictionary and these user words."""
    return state is not None and (state.dictionary_sha1, state.user_words_digest) == (
        DICTIONARY_BLOB_SHA1,
        words_digest,
    )


def _plan(
    entries_are_current: bool, words_are_current: bool, has_new_documents: bool
) -> IndexUpdate:
    """Rebuild only what changed: entries depend on the layout and the model, words on the
    tokenizer."""
    if not entries_are_current:
        return IndexUpdate.ALL
    if not words_are_current:
        return IndexUpdate.KEYWORDS
    if has_new_documents:
        return IndexUpdate.WRITTEN_FILES
    return IndexUpdate.NONE


def _loaded(model: "SentenceTransformer | None") -> "SentenceTransformer":
    # ingest_folder loads the model whenever a run writes files or the embeddings are stale.
    if model is None:
        raise RuntimeError("the embedding model is needed but was not loaded")
    return model


async def _store(
    session: AsyncSession,
    prepared: Sequence[_Prepared],
    stale_paths: Sequence[str],
    synonyms: Synonyms,
    model: "SentenceTransformer | None",
    report: IngestReport,
) -> None:
    tokenizer_state = await session.get(TokenizerState, TOKENIZER_STATE_ID)
    embedding_state = await session.get(EmbeddingState, EMBEDDING_STATE_ID)
    layout_state = await session.get(EntryLayoutState, ENTRY_LAYOUT_STATE_ID)
    replaced_paths = [item.candidate.source_path for item in prepared] + list(
        stale_paths
    )
    if replaced_paths:
        await session.execute(
            delete(Document).where(Document.source_path.in_(replaced_paths))
        )
    new_document_ids = [await _insert(session, item, report) for item in prepared]

    tokenizer = build_tokenizer(await user_words(session, synonyms))
    report.index_update = _plan(
        _entries_are_current(embedding_state, layout_state),
        _words_are_current(tokenizer_state, tokenizer.user_words_digest),
        bool(new_document_ids),
    )
    if report.index_update == IndexUpdate.ALL:
        await session.execute(delete(SearchEntry))
        await _add_entries(session, tokenizer, _loaded(model), None)
    else:
        # Rebuild the old entries' words before the new entries are added, so no entry is
        # tokenized twice.
        if report.index_update == IndexUpdate.KEYWORDS:
            await _rebuild_words(session, tokenizer)
        if new_document_ids:
            await _add_entries(session, tokenizer, _loaded(model), new_document_ids)

    await session.merge(
        TokenizerState(
            id=TOKENIZER_STATE_ID,
            dictionary_sha1=DICTIONARY_BLOB_SHA1,
            user_words_digest=tokenizer.user_words_digest,
        )
    )
    await session.merge(
        EmbeddingState(
            id=EMBEDDING_STATE_ID, model_name=MODEL_NAME, model_revision=MODEL_REVISION
        )
    )
    await session.merge(EntryLayoutState(id=ENTRY_LAYOUT_STATE_ID, layout=ENTRY_LAYOUT))


async def ingest_folder(root: Path) -> IngestReport:
    """Ingest every supported file under `root`. Paths are stored relative to `root`."""
    report = IngestReport()
    candidates = _collect(root, report)
    synonyms = load_synonyms()
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
            entries_are_current = _entries_are_current(
                await session.get(EmbeddingState, EMBEDDING_STATE_ID),
                await session.get(EntryLayoutState, ENTRY_LAYOUT_STATE_ID),
            )
            words_are_current = _words_are_current(
                await session.get(TokenizerState, TOKENIZER_STATE_ID),
                user_words_digest(await user_words(session, synonyms)),
            )

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
        if (
            not prepared
            and not stale_paths
            and entries_are_current
            and words_are_current
        ):
            return report

        # Load the model before the transaction opens: the first run downloads it. A run
        # that only removes files or changes words embeds nothing, so it loads no model.
        model = load_model() if prepared or not entries_are_current else None
        async with sessions() as session, session.begin():
            await _store(session, prepared, stale_paths, synonyms, model, report)
            # A connection reports its dead-row counts to the table statistics at most once a
            # second, so the write's count could arrive after VACUUM has reported the table
            # clean, and the statistics would show dead rows that are already gone. This makes
            # the write report when its transaction ends, before VACUUM runs.
            await session.execute(text("SELECT pg_stat_force_next_flush()"))
        await vacuum(engine)
    return report


async def knowledge_base_is_empty() -> bool:
    """Whether nothing has been ingested yet: the states an ingest writes are not there.

    Raises SchemaMismatchError for a database made by another version of chat-bridge.
    """
    async with open_engine() as engine:
        await create_tables(engine)
        async with async_sessionmaker(engine)() as session:
            tokenizer_state = await session.get(TokenizerState, TOKENIZER_STATE_ID)
            embedding_state = await session.get(EmbeddingState, EMBEDDING_STATE_ID)
    return tokenizer_state is None or embedding_state is None
