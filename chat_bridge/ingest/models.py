"""Tables of the knowledge base. Model shape follows the Azure rag-postgres template."""

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
    SECTION = "section"  # the section's heading path and content
    KEYWORDS = "keywords"  # every name in the document's keyword groups


class Document(Base):
    """One ingested file. `content_hash` is the SHA-256 of the file bytes."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_path: Mapped[str] = mapped_column(unique=True)
    content_hash: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    keyword_groups: Mapped[list[list[str]]] = mapped_column(JSONB)


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
    that all point at the paragraph, a section has one row for its own text, and the
    document's first section also has one row for the document's keyword groups. So a
    keyword name finds the document's first section, not every section of it.

    Each row holds both the words and the embedding of the same text, as MaxKB's rows hold
    `search_vector` and `embedding`. A text too long for the model becomes several rows.
    The embedding column is named after its model, as in the Azure template.

    The row keeps the text it was built from. When only the tokenizer changes, the words
    are rebuilt from it and the embedding is kept.
    """

    __tablename__ = "search_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    search_vector: Mapped[str] = mapped_column(TSVECTOR)
    embedding_bge_m3: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS))

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
