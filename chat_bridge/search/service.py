"""Full-text search over the stored sections.

The query shape follows the full-text half of the Azure rag-postgres template: rank with
ts_rank_cd, then load the ranked rows by id. The query text comes from the same jieba
tokenizer that built the index (MaxKB's websearch_to_tsquery with the `simple` configuration).
"""

from dataclasses import dataclass

from sqlalchemy import Float, Integer, column, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from chat_bridge.database import create_tables, open_engine
from chat_bridge.ingest import service as ingest_service
from chat_bridge.ingest.models import Document, Section, TokenizerState
from chat_bridge.tokenizer import DICTIONARY_BLOB_SHA1, build_tokenizer, query_clauses

# As MaxKB's keywords_search.sql: rank every matching entry, keep the best entry of each
# section, then order the sections. Normalization 32 maps the rank into 0..1 as
# rank / (rank + 1).
FULLTEXT_QUERY = text(
    """
    SELECT best.section_id AS id, best.rank
    FROM (
        SELECT DISTINCT ON (entries.section_id)
            entries.section_id, ts_rank_cd(entries.search_vector, query, 32) AS rank
        FROM search_entries entries, websearch_to_tsquery('simple', :query) query
        WHERE entries.search_vector @@ query
        ORDER BY entries.section_id, rank DESC
    ) best
    ORDER BY best.rank DESC, best.section_id
    LIMIT :limit
    """
).columns(column("id", Integer), column("rank", Float))

SNIPPET_RADIUS = 60


class EmptyKnowledgeBaseError(Exception):
    """Nothing has been ingested yet."""


class IndexMismatchError(Exception):
    """The stored search vectors were built with another dictionary or other user words."""


@dataclass(frozen=True)
class SearchHit:
    source_path: str
    title: str
    heading: str
    snippet: str
    rank: float


@dataclass(frozen=True)
class SearchResult:
    query: str
    hits: list[SearchHit]


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


async def search(question: str, limit: int) -> SearchResult:
    """Return the best-ranked sections for the question. No hits means the data has no match."""
    async with open_engine() as engine:
        await create_tables(engine)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            state = await session.get(TokenizerState, ingest_service.TOKENIZER_STATE_ID)
            if state is None:
                raise EmptyKnowledgeBaseError

            tokenizer = build_tokenizer(await ingest_service.stored_user_words(session))
            if (state.dictionary_sha1, state.user_words_digest) != (
                DICTIONARY_BLOB_SHA1,
                tokenizer.user_words_digest,
            ):
                raise IndexMismatchError

            clauses = query_clauses(tokenizer, question)
            query = " or ".join(clauses)
            if not clauses:
                return SearchResult(query, [])

            ranked = (
                await session.execute(FULLTEXT_QUERY, {"query": query, "limit": limit})
            ).all()
            if not ranked:
                return SearchResult(query, [])

            rows = await session.execute(
                select(Section, Document.source_path, Document.title)
                .join(Document, Section.document_id == Document.id)
                .where(Section.id.in_([row.id for row in ranked]))
            )
            by_id = {row.Section.id: row for row in rows}

    hits = [
        SearchHit(
            source_path=by_id[row.id].source_path,
            title=by_id[row.id].title,
            heading=by_id[row.id].Section.heading,
            snippet=_snippet(by_id[row.id].Section.content, clauses),
            rank=row.rank,
        )
        for row in ranked
    ]
    return SearchResult(query, hits)
