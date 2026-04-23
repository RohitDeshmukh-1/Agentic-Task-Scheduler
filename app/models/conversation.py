"""ConversationMemory — stores recent conversation context per user for the LLM."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class ConversationMemory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversation_memory"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Memory {self.role}: {self.content[:40]}>"
