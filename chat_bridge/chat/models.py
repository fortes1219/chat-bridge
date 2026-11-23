"""The chat's own table: one row per question asked."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from chat_bridge.database import Base

# A record whose search found no section. The list of these reads a partial index with exactly
# this condition, so it does not scan every record. The query must use the same text for the
# planner to match it to the index.
UNANSWERED = "jsonb_array_length(details -> 'sections') = 0"


class ChatRecord(Base):
    """One question and what came back.

    `details` keeps what is needed to check an answer afterwards: the sections the search
    found, the text and the command line Claude Code was given, and the error when the answer
    failed.

    A question the search found nothing for has an empty section list. Those are the questions
    the data cannot answer, the list of what to add next, so the empty list is the mark and
    there is no separate flag.
    """

    __tablename__ = "chat_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    question: Mapped[str] = mapped_column()
    answer: Mapped[str] = mapped_column()
    details: Mapped[dict[str, Any]] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_chat_records_unanswered", "id", postgresql_where=text(UNANSWERED)),
    )
