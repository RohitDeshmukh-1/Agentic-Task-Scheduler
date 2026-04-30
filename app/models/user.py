"""User model — stores profile, preferences, and gamification metrics."""

from __future__ import annotations

from datetime import time
from typing import Optional

from sqlalchemy import Float, Integer, String, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # ── Identity ─────────────────────────────────────────────────────────
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")

    # ── Gamification ─────────────────────────────────────────────────────
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)

    # ── Preferences ──────────────────────────────────────────────────────
    preferred_reminder_time: Mapped[Optional[time]] = mapped_column(
        Time, default=time(8, 0)
    )
    preferred_check_time: Mapped[Optional[time]] = mapped_column(
        Time, default=time(21, 0)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    dormant_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    consecutive_ignores: Mapped[int] = mapped_column(Integer, default=0)

    # ── Relationships ────────────────────────────────────────────────────
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    recurring_tasks = relationship(
        "RecurringTask", back_populates="user", cascade="all, delete-orphan"
    )
    daily_logs = relationship(
        "DailyLog", back_populates="user", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "ConversationMemory", back_populates="user", cascade="all, delete-orphan"
    )
    memory_logs = relationship(
        "MemoryLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.phone_number} streak={self.current_streak}>"
