"""DailyLog CRUD with analytics queries."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog


class DailyLogCRUD:

    @staticmethod
    async def upsert(
        db: AsyncSession,
        user_id: str,
        log_date: date,
        total: int,
        completed: int,
        missed: int,
        rescheduled: int,
        xp: int,
    ) -> DailyLog:
        """Create or update the daily log for a user on a given date."""
        result = await db.execute(
            select(DailyLog).where(
                and_(DailyLog.user_id == user_id, DailyLog.date == log_date)
            )
        )
        log = result.scalar_one_or_none()

        if log:
            log.total_tasks = total
            log.completed_tasks = completed
            log.missed_tasks = missed
            log.rescheduled_tasks = rescheduled
            log.completion_rate = completed / total if total > 0 else 0.0
            log.xp_earned = xp
        else:
            log = DailyLog(
                user_id=user_id,
                date=log_date,
                total_tasks=total,
                completed_tasks=completed,
                missed_tasks=missed,
                rescheduled_tasks=rescheduled,
                completion_rate=completed / total if total > 0 else 0.0,
                xp_earned=xp,
            )
            db.add(log)

        await db.flush()
        return log

    @staticmethod
    async def get_for_date(
        db: AsyncSession, user_id: str, log_date: date
    ) -> Optional[DailyLog]:
        result = await db.execute(
            select(DailyLog).where(
                and_(DailyLog.user_id == user_id, DailyLog.date == log_date)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_range(
        db: AsyncSession, user_id: str, start: date, end: date
    ) -> list[DailyLog]:
        result = await db.execute(
            select(DailyLog)
            .where(
                and_(
                    DailyLog.user_id == user_id,
                    DailyLog.date >= start,
                    DailyLog.date <= end,
                )
            )
            .order_by(DailyLog.date)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_weekly_stats(db: AsyncSession, user_id: str, ref_date: date) -> dict:
        """Get aggregated stats for the week containing ref_date."""
        # Find Monday of the week
        week_start = ref_date - timedelta(days=ref_date.weekday())
        week_end = week_start + timedelta(days=6)

        logs = await DailyLogCRUD.get_range(db, user_id, week_start, week_end)

        total = sum(l.total_tasks for l in logs)
        completed = sum(l.completed_tasks for l in logs)
        missed = sum(l.missed_tasks for l in logs)
        rescheduled = sum(l.rescheduled_tasks for l in logs)
        xp = sum(l.xp_earned for l in logs)

        return {
            "week_start": week_start,
            "week_end": week_end,
            "total_tasks": total,
            "completed_tasks": completed,
            "missed_tasks": missed,
            "rescheduled_tasks": rescheduled,
            "completion_rate": completed / total if total > 0 else 0.0,
            "xp_earned": xp,
            "daily_logs": logs,
        }

    @staticmethod
    async def get_consistency_score(db: AsyncSession, user_id: str, days: int = 30) -> float:
        """Calculate consistency score over the last N days."""
        end = date.today()
        start = end - timedelta(days=days)
        logs = await DailyLogCRUD.get_range(db, user_id, start, end)

        if not logs:
            return 0.0

        rates = [l.completion_rate for l in logs]
        return sum(rates) / len(rates)
