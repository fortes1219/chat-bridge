"""Hybrid search over the stored sections: keyword ranking and vector ranking, merged.

The query follows the hybrid search of the Azure rag-postgres template: each method ranks its
best candidates, and Reciprocal Rank Fusion merges the two lists. The keyword query comes from
the same jieba tokenizer that built the index, and the question is embedded with the same
model as the documents.

In the Azure template one row is one item. Here, as in MaxKB, several search entries point
at one section, and the section is the item: each method first keeps every section's best
entry, then the two lists are merged by section.
"""

from dataclasses import dataclass

from sqlalchemy import Float, Integer, column, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from chat_bridge.database import create_tables, open_engine
from chat_bridge.embedding import MODEL_NAME, MODEL_REVISION, embed_query, load_model
from chat_bridge.ingest import service as ingest_service
from chat_bridge.ingest.models import Document, EmbeddingState, Section, TokenizerState
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

HYBRID_QUERY = text(
    """
    WITH vector_entries AS (
        SELECT section_id, embedding_bge_m3 <=> :embedding AS distance
        FROM search_entries
        WHERE 1 - (embedding_bge_m3 <=> :embedding) > :min_similarity
        ORDER BY embedding_bge_m3 <=> :embedding
        LIMIT :candidates
    ),
    vector_search AS (
        SELECT section_id, RANK () OVER (ORDER BY MIN(distance)) AS rank
        FROM vector_entries
        GROUP BY section_id
    ),
    fulltext_entries AS (
        SELECT section_id, ts_rank_cd(search_vector, query, 32) AS relevance
        FROM search_entries, websearch_to_tsquery('simple', :query) query
        WHERE search_vector @@ query
        ORDER BY ts_rank_cd(search_vector, query, 32) DESC
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

SNIPPET_RADIUS = 60


class EmptyKnowledgeBaseError(Exception):
    """Nothing has been ingested yet."""


class IndexMismatchError(Exception):
    """The stored entries were built with another dictionary, other user words, or another model."""


@dataclass(frozen=True)
class SearchHit:
    source_path: str
    title: str
    heading: str
    snippet: str
    score: float
    # The section's rank in each method's candidate list; None when that method missed it.
    keyword_rank: int | None
    vector_rank: int | None


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

            tokenizer = build_tokenizer(
                await ingest_service.user_words(session, synonyms)
            )
            stored = (
                tokenizer_state.dictionary_sha1,
                tokenizer_state.user_words_digest,
                embedding_state.model_name,
                embedding_state.model_revision,
            )
            current = (
                DICTIONARY_BLOB_SHA1,
                tokenizer.user_words_digest,
                MODEL_NAME,
                MODEL_REVISION,
            )
            if stored != current:
                raise IndexMismatchError

            clauses = query_clauses(tokenizer, question, synonyms.expand(question))
            query = " or ".join(clauses)
            embedding = embed_query(load_model(), question)
            ranked = (
                await session.execute(
                    HYBRID_QUERY,
                    {
                        "query": query,
                        "embedding": embedding,
                        "min_similarity": MIN_SIMILARITY,
                        "candidates": CANDIDATES_PER_METHOD,
                        "k": RRF_K,
                        "limit": limit,
                    },
                )
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
            score=row.score,
            keyword_rank=row.keyword_rank,
            vector_rank=row.vector_rank,
        )
        for row in ranked
    ]
    return SearchResult(query, hits)
