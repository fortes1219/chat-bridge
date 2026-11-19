"""Tables of the knowledge base. Model shape follows the Azure rag-postgres template."""

from enum import StrEnum

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from chat_bridge.database import Base

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
    """

    __tablename__ = "search_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column()
    search_vector: Mapped[str] = mapped_column(TSVECTOR)

    __table_args__ = (
        Index(
            "ix_search_entries_search_vector", "search_vector", postgresql_using="gin"
        ),
    )


class TokenizerState(Base):
    """The tokenizer the stored search vectors were built with. There is one row, id 1.

    The dictionary and the user words are kept apart: user words change only when a document
    changes, so a run without changes only has to compare the dictionary.
    """

    __tablename__ = "tokenizer_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    dictionary_sha1: Mapped[str] = mapped_column()
    user_words_digest: Mapped[str] = mapped_column()
