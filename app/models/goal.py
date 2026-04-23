"""Goal model — long-term objectives that tasks roll up into."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin

import enum


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class Goal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "goals"

    # ── Fields ───────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus), default=GoalStatus.ACTIVE
    )
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Goal '{self.title}' status={self.status.value}>"
