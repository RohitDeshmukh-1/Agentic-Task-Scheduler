"""RecurringTask model — stores repeating task rules."""

from __future__ import annotations

import enum
from datetime import date, time
from typing import Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class RecurrenceFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class RecurringTask(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recurring_tasks"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="other")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    scheduled_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency), default=RecurrenceFrequency.DAILY
    )
    days_of_week: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    except_days: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    last_generated_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="recurring_tasks")

    def __repr__(self) -> str:
        return f"<RecurringTask '{self.description[:30]}' freq={self.frequency.value}>"
