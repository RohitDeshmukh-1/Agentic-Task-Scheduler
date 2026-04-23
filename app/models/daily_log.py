"""DailyLog model — daily productivity metrics for analytics and gamification."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class DailyLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "daily_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date"),
    )

    # ── Fields ───────────────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    missed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    rescheduled_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    mood: Mapped[str] = mapped_column(String(20), default="neutral")

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="daily_logs")

    def __repr__(self) -> str:
        return f"<DailyLog {self.date} rate={self.completion_rate:.0%}>"
