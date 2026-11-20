"""Tables of the knowledge base. Model shape follows the Azure rag-postgres template."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from chat_bridge.database import Base
from chat_bridge.embedding import DIMENSIONS

# The section that document-wide search text points at.
LEAD_SECTION_POSITION = 0


class EntrySource(StrEnum):
    SECTION = "section"  # the section's heading path and its content outside tables
    KEYWORDS = "keywords"  # every name in the document's keyword groups
    TABLE = "table"  # the section's heading path and one of its tables


@dataclass(frozen=True)
class SourceRule:
    # The keyword-ranking weight, as a tsvector weight label.
    weight: str
    # Whether the entry is embedded and so takes part in vector search.
    embedded: bool


# With no weights given, ts_rank_cd uses {D, C, B, A} = {0.1, 0.2, 0.4, 1.0} (PostgreSQL
# manual, "Ranking Search Results"), so a word in a table counts a tenth of a word in the
# text. A table still matches every word it holds; it only ranks below text with the same
# words. A table is not embedded: LlamaIndex does not embed a raw table either, it embeds a
# summary written by a model and links the table to it. There is no such summary here, so a
# table takes part in keyword search only.
SOURCE_RULES: dict[EntrySource, SourceRule] = {
    EntrySource.SECTION: SourceRule(weight="A", embedded=True),
    EntrySource.KEYWORDS: SourceRule(weight="A", embedded=True),
    EntrySource.TABLE: SourceRule(weight="D", embedded=False),
}

# How entries are cut from sections and treated. Any change to the sources or their rules
# changes this text, and a stored index with another layout is rebuilt in full.
ENTRY_LAYOUT = ";".join(
    f"{source}:{rule.weight}:{'embedded' if rule.embedded else 'words'}"
    for source, rule in SOURCE_RULES.items()
)


class Document(Base):
    """One ingested file. `content_hash` is the SHA-256 of the file bytes.

    `event_date` comes from the front matter. Word and PDF files have none, so it is None.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(unique=True)
    content_hash: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    keyword_groups: Mapped[list[list[str]]] = mapped_column(JSONB)
    event_date: Mapped[date | None] = mapped_column()


class Section(Base):
    """One section of a document, split at a heading. Deleting the document deletes its sections."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column()
    heading: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()

    __table_args__ = (UniqueConstraint("document_id", "position"),)


class SearchEntry(Base):
    """A text that finds one section.

    As in MaxKB, where a paragraph's own text and its related questions are separate rows
    that all point at the paragraph, a section has one row for its own text, one row for
    each of its tables, and the document's first section also has one row for the
    document's keyword groups. So a keyword name finds the document's first section, not
    every section of it.

    Each row holds both the words and the embedding of the same text, as MaxKB's rows hold
    `search_vector` and `embedding`. A text too long for the model becomes several rows.
    The embedding column is named after its model, as in the Azure template.

    The row keeps the text it was built from. When only the tokenizer changes, the words
    are rebuilt from it and the embedding is kept. A row whose source is not embedded
    (SOURCE_RULES) has no embedding, so the vector index never holds it.
    """

    __tablename__ = "search_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    search_vector: Mapped[str] = mapped_column(TSVECTOR)
    embedding_bge_m3: Mapped[list[float] | None] = mapped_column(Vector(DIMENSIONS))

    __table_args__ = (
        Index(
            "ix_search_entries_search_vector", "search_vector", postgresql_using="gin"
        ),
        # HNSW with cosine distance, with the Azure template's parameters.
        Index(
            "ix_search_entries_embedding_bge_m3",
            "embedding_bge_m3",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding_bge_m3": "vector_cosine_ops"},
        ),
    )


class TokenizerState(Base):
    """The tokenizer the stored search vectors were built with. There is one row, id 1."""

    __tablename__ = "tokenizer_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    dictionary_sha1: Mapped[str] = mapped_column()
    user_words_digest: Mapped[str] = mapped_column()


class EmbeddingState(Base):
    """The model the stored embeddings were built with. There is one row, id 1.

    A search embeds the question with its own model, and refuses to compare it with
    embeddings from another model, as RAGFlow ties one embedding model to a knowledge base.
    """

    __tablename__ = "embedding_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column()
    model_revision: Mapped[str] = mapped_column()


class EntryLayoutState(Base):
    """The entry layout the stored entries were cut with. There is one row, id 1.

    A database made before this table existed gets it from create_all, without the row, so
    its entries count as cut with an older layout and are rebuilt.
    """

    __tablename__ = "entry_layout_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    layout: Mapped[str] = mapped_column()
