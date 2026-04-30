"""Task model — daily actionable items with priority, difficulty, and recurrence."""

from __future__ import annotations

import enum
from datetime import date, time
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


class TaskDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCategory(str, enum.Enum):
    WORK = "work"
    STUDY = "study"
    PERSONAL = "personal"
    HEALTH = "health"
    FINANCE = "finance"
    CHORES = "chores"
    SOCIAL = "social"
    OTHER = "other"


class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    # ── Core Fields ──────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    goal_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )
    recurring_task_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("recurring_tasks.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TaskCategory] = mapped_column(
        Enum(TaskCategory), default=TaskCategory.OTHER
    )
    difficulty: Mapped[TaskDifficulty] = mapped_column(
        Enum(TaskDifficulty), default=TaskDifficulty.MEDIUM
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM
    )

    # ── Scheduling ───────────────────────────────────────────────────────
    scheduled_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    scheduled_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, index=True
    )
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── XP Reward (Gamification) ─────────────────────────────────────────
    xp_reward: Mapped[int] = mapped_column(Integer, default=10)

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    recurring_task = relationship("RecurringTask")

    def __repr__(self) -> str:
        return f"<Task '{self.description[:30]}' date={self.scheduled_date} status={self.status.value}>"

    def calculate_xp(self) -> int:
        """Dynamic XP based on difficulty and priority."""
        difficulty_map = {TaskDifficulty.EASY: 5, TaskDifficulty.MEDIUM: 10, TaskDifficulty.HARD: 20}
        priority_map = {TaskPriority.LOW: 1, TaskPriority.MEDIUM: 1.5, TaskPriority.HIGH: 2, TaskPriority.URGENT: 3}
        return int(difficulty_map.get(self.difficulty, 10) * priority_map.get(self.priority, 1))
