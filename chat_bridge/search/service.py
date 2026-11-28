"""Hybrid search over the stored sections: keyword ranking and vector ranking, merged.

The query follows the hybrid search of the Azure rag-postgres template: each method ranks its
best candidates, and Reciprocal Rank Fusion merges the two lists. The keyword query comes from
the same jieba tokenizer that built the index, and the question is embedded with the same
model as the documents.

In the Azure template one row is one item. Here, as in MaxKB, several search entries point
at one section, and the section is the item: each method first keeps every section's best
entry, then the two lists are merged by section.

A search can be limited to events on or before a date. As the Azure template filters inside
each method's candidate query, the date filter is applied before the candidates are taken,
so later events cannot fill the candidate lists. The filter works on whole files by their
event date: a file's own later sections, such as what happened in the days after the event,
are not removed from it.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import Float, Integer, Row, column, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chat_bridge.database import create_tables, open_engine
from chat_bridge.embedding import MODEL_NAME, MODEL_REVISION, embed_queries, load_model
from chat_bridge.ingest import service as ingest_service
from chat_bridge.ingest.models import (
    ENTRY_LAYOUT,
    Document,
    EmbeddingState,
    EntryLayoutState,
    Section,
    TokenizerState,
)
from chat_bridge.synonyms import load_synonyms
from chat_bridge.tokenizer import DICTIONARY_BLOB_SHA1, build_tokenizer, query_clauses

# The Azure template takes 20 candidates from each method and fuses them with k = 60.
CANDIDATES_PER_METHOD = 20
RRF_K = 60
# The lowest similarity (1 - cosine distance) a vector candidate may have. The model's authors
# say to choose a threshold from the similarity distribution on one's own data (FlagEmbedding
# research/baai_general_embedding/README.md). On these 71 files, questions the data does not
# cover reached at most 0.511 and questions it covers at least 0.524, so the line is 0.52.
# The gap is thin: the line only keeps out questions that have nothing to do with the data.
# Measure again when the data changes.
MIN_SIMILARITY = 0.52

# Keeps the entries of files whose event happened on or before :as_of; a NULL :as_of keeps
# every file. A file without an event date fails the comparison, as PostgreSQL's comparison
# operators yield null for a null input, so it is left out of a dated search.
AVAILABLE_ON_DATE = (
    "(CAST(:as_of AS date) IS NULL OR documents.event_date <= CAST(:as_of AS date))"
)

# pgvector's README: with an approximate index the filter runs after the index scan, so
# iterative scans keep scanning until enough rows pass; and for a filter on distance, take
# the nearest rows in a MATERIALIZED CTE, other filters inside it, and the distance filter
# outside. Rows with no embedding, which are tables, never enter the vector side.
HYBRID_QUERY = text(
    f"""
    WITH vector_entries AS MATERIALIZED (
        SELECT entries.section_id, entries.embedding_bge_m3 <=> :embedding AS distance
        FROM search_entries entries
        JOIN sections ON sections.id = entries.section_id
        JOIN documents ON documents.id = sections.document_id
        WHERE entries.embedding_bge_m3 IS NOT NULL AND {AVAILABLE_ON_DATE}
        ORDER BY entries.embedding_bge_m3 <=> :embedding
        LIMIT :candidates
    ),
    vector_search AS (
        SELECT section_id, RANK () OVER (ORDER BY MIN(distance)) AS rank
        FROM vector_entries
        WHERE 1 - distance > :min_similarity
        GROUP BY section_id
    ),
    fulltext_entries AS (
        SELECT entries.section_id, ts_rank_cd(entries.search_vector, query, 32) AS relevance
        FROM search_entries entries
        JOIN sections ON sections.id = entries.section_id
        JOIN documents ON documents.id = sections.document_id
        CROSS JOIN websearch_to_tsquery('simple', :query) query
        WHERE entries.search_vector @@ query AND {AVAILABLE_ON_DATE}
        ORDER BY relevance DESC
        LIMIT :candidates
    ),
    fulltext_search AS (
        SELECT section_id, RANK () OVER (ORDER BY MAX(relevance) DESC) AS rank
        FROM fulltext_entries
        GROUP BY section_id
    )
    SELECT
        COALESCE(vector_search.section_id, fulltext_search.section_id) AS id,
        COALESCE(1.0 / (:k + vector_search.rank), 0.0)
            + COALESCE(1.0 / (:k + fulltext_search.rank), 0.0) AS score,
        vector_search.rank AS vector_rank,
        fulltext_search.rank AS keyword_rank
    FROM vector_search
    FULL OUTER JOIN fulltext_search ON vector_search.section_id = fulltext_search.section_id
    ORDER BY score DESC, id
    LIMIT :limit
    """
).columns(
    column("id", Integer),
    column("score", Float),
    column("vector_rank", Integer),
    column("keyword_rank", Integer),
)
# Strict ordering keeps the vector candidates in exact distance order (pgvector 0.8.0 and later).
ITERATIVE_SCAN = text("SET LOCAL hnsw.iterative_scan = strict_order")

SNIPPET_RADIUS = 60


class EmptyKnowledgeBaseError(Exception):
    """Nothing has been ingested yet."""


class IndexMismatchError(Exception):
    """The stored entries were built with another dictionary, other user words, another
    model, or another entry layout."""


@dataclass(frozen=True)
class SearchHit:
    section_id: int
    source_path: str
    title: str
    event_date: date | None
    heading: str
    snippet: str
    # The document's markets, its own first, and its moment, when its front matter gives them.
    markets: tuple[str, ...]
    event_time: datetime | None
    # The section's whole text, which a chat answer reads; the snippet is what a list shows.
    content: str
    score: float
    # The section's rank in each method's candidate list; None when that method missed it.
    keyword_rank: int | None
    vector_rank: int | None


@dataclass(frozen=True)
class SearchResult:
    query: str
    hits: list[SearchHit]
    # Files left out of a dated search because they have no event date; 0 without a date.
    undated_left_out: int = 0


def _snippet(content: str, clauses: list[str]) -> str:
    """A window of the content around the first word of the query that it contains."""
    flat = " ".join(content.split())
    lowered = flat.lower()
    words = [word.lower() for clause in clauses for word in clause.split()]
    found = [
        position for position in (lowered.find(word) for word in words) if position >= 0
    ]
    start = max(min(found) - SNIPPET_RADIUS, 0) if found else 0
    end = min(start + 2 * SNIPPET_RADIUS, len(flat))
    return (
        ("…" if start > 0 else "") + flat[start:end] + ("…" if end < len(flat) else "")
    )


async def _undated_files(session: AsyncSession) -> int:
    """How many stored files have no event date, and so are left out of a dated search."""
    count = await session.scalar(
        select(func.count()).select_from(Document).where(Document.event_date.is_(None))
    )
    return count or 0


async def search(
    question: str,
    limit: int,
    as_of: date | None = None,
    *,
    candidates: int = CANDIDATES_PER_METHOD,
) -> SearchResult:
    """Return the best-ranked sections for the question. No hits means the data has no match.

    With `as_of`, only files whose event happened on or before that day are searched.
    `candidates` is how many each method ranks before the two lists are merged.
    """
    [result] = await search_many([question], limit, as_of, candidates=candidates)
    return result


async def search_many(
    questions: Sequence[str],
    limit: int,
    as_of: date | None = None,
    *,
    candidates: int = CANDIDATES_PER_METHOD,
) -> list[SearchResult]:
    """Search each question as `search()` does, in one session.

    The stored state is checked and the tokenizer built once, and the questions are embedded in
    one batched call, so each further question costs its own query and little else.
    """
    if not questions:
        return []
    synonyms = load_synonyms()
    async with open_engine() as engine:
        await create_tables(engine)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            tokenizer_state = await session.get(
                TokenizerState, ingest_service.TOKENIZER_STATE_ID
            )
            embedding_state = await session.get(
                EmbeddingState, ingest_service.EMBEDDING_STATE_ID
            )
            if tokenizer_state is None or embedding_state is None:
                raise EmptyKnowledgeBaseError
            # A database from before entry layouts were recorded has no layout row.
            layout_state = await session.get(
                EntryLayoutState, ingest_service.ENTRY_LAYOUT_STATE_ID
            )

            tokenizer = build_tokenizer(
                await ingest_service.user_words(session, synonyms)
            )
            stored = (
                tokenizer_state.dictionary_sha1,
                tokenizer_state.user_words_digest,
                embedding_state.model_name,
                embedding_state.model_revision,
                layout_state.layout if layout_state else None,
            )
            current = (
                DICTIONARY_BLOB_SHA1,
                tokenizer.user_words_digest,
                MODEL_NAME,
                MODEL_REVISION,
                ENTRY_LAYOUT,
            )
            if stored != current:
                raise IndexMismatchError

            embeddings = embed_queries(load_model(), questions)
            undated_left_out = 0 if as_of is None else await _undated_files(session)
            await session.execute(ITERATIVE_SCAN)
            results = []
            for question, embedding in zip(questions, embeddings, strict=True):
                clauses = query_clauses(tokenizer, question, synonyms.expand(question))
                query = " or ".join(clauses)
                ranked = (
                    await session.execute(
                        HYBRID_QUERY,
                        {
                            "query": query,
                            "embedding": embedding,
                            "as_of": as_of,
                            "min_similarity": MIN_SIMILARITY,
                            "candidates": candidates,
                            "k": RRF_K,
                            "limit": limit,
                        },
                    )
                ).all()
                hits = await _hits(session, ranked, clauses)
                results.append(SearchResult(query, hits, undated_left_out))
    return results


async def _hits(
    session: AsyncSession, ranked: Sequence[Row[Any]], clauses: list[str]
) -> list[SearchHit]:
    """The ranked rows as hits, in rank order, each with its section's text and file."""
    if not ranked:
        return []
    rows = await session.execute(
        select(
            Section,
            Document.source_path,
            Document.title,
            Document.event_date,
            Document.markets,
            Document.event_time,
        )
        .join(Document, Section.document_id == Document.id)
        .where(Section.id.in_([row.id for row in ranked]))
    )
    by_id = {row.Section.id: row for row in rows}
    return [
        SearchHit(
            section_id=row.id,
            source_path=by_id[row.id].source_path,
            title=by_id[row.id].title,
            event_date=by_id[row.id].event_date,
            heading=by_id[row.id].Section.heading,
            snippet=_snippet(by_id[row.id].Section.content, clauses),
            markets=tuple(by_id[row.id].markets),
            event_time=by_id[row.id].event_time,
            content=by_id[row.id].Section.content,
            score=row.score,
            keyword_rank=row.keyword_rank,
            vector_rank=row.vector_rank,
        )
        for row in ranked
    ]


async def latest_event_date() -> date | None:
    """The latest event date in the whole knowledge base: the date the data reaches.

    One indexed query, whatever any search found.
    """
    async with open_engine() as engine:
        await create_tables(engine)
        sessions = async_sessionmaker(engine)
        async with sessions() as session:
            latest: date | None = await session.scalar(
                select(func.max(Document.event_date))
            )
    return latest
