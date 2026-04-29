"""ConversationMemory — stores conversation history with intent and metadata."""

from __future__ import annotations

from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin
import enum


class ConversationIntent(str, enum.Enum):
    """Intent categories for memory tagging."""
    SCHEDULING = "scheduling"
    STATUS_UPDATE = "status_update"
    GOAL_SETTING = "goal_setting"
    PLANNING = "planning"
    ANALYSIS = "analysis"
    LOGGING = "logging"
    SUGGESTION_REQUEST = "suggestion_request"
    QUERY = "query"
    OTHER = "other"


class ConversationMemory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversation_memory"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ── Metadata ─────────────────────────────────────────────────────────
    intent: Mapped[Optional[str]] = mapped_column(
        Enum(ConversationIntent), nullable=True, default=None
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # comma-separated
    
    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        intent_str = f" [{self.intent.value}]" if self.intent else ""
        return f"<Memory {self.role}{intent_str}: {self.content[:40]}>"


class MemoryLog(UUIDMixin, TimestampMixin, Base):
    """User-created memory logs for personal planning and task notes."""
    __tablename__ = "memory_logs"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    log_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # task_note, plan, reflection, milestone, etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ── Metadata ─────────────────────────────────────────────────────────
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(default=1)  # 1-5 scale
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # comma-separated
    linked_task_ids: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # comma-separated UUIDs
    
    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="memory_logs")

    def __repr__(self) -> str:
        return f"<MemoryLog {self.log_type}: {self.content[:40]}>"
