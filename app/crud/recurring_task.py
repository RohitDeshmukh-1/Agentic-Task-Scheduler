"""RecurringTask CRUD operations."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring_task import RecurringTask


class RecurringTaskCRUD:

    @staticmethod
    async def create(db: AsyncSession, user_id: str, data: dict) -> RecurringTask:
        task = RecurringTask(user_id=user_id, **data)
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def list_active(db: AsyncSession) -> list[RecurringTask]:
        result = await db.execute(
            select(RecurringTask).where(RecurringTask.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_active_for_user(db: AsyncSession, user_id: str) -> list[RecurringTask]:
        result = await db.execute(
            select(RecurringTask).where(
                and_(
                    RecurringTask.user_id == user_id,
                    RecurringTask.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_last_generated(
        db: AsyncSession,
        recurring_id: str,
        last_date: date,
    ) -> Optional[RecurringTask]:
        result = await db.execute(
            select(RecurringTask).where(RecurringTask.id == recurring_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        task.last_generated_date = last_date
        await db.flush()
        return task
