"""Task CRUD with smart rescheduling and batch operations."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskDifficulty
from app.schemas.task import TaskCreate, TaskUpdate


class TaskCRUD:

    @staticmethod
    async def create(db: AsyncSession, user_id: str, data: TaskCreate) -> Task:
        task = Task(user_id=user_id, **data.model_dump())
        task.xp_reward = task.calculate_xp()
        db.add(task)
        await db.flush()
        return task

    @staticmethod
    async def create_many(db: AsyncSession, user_id: str, tasks: list[TaskCreate]) -> list[Task]:
        created = []
        for data in tasks:
            task = Task(user_id=user_id, **data.model_dump())
            task.xp_reward = task.calculate_xp()
            db.add(task)
            created.append(task)
        await db.flush()
        return created

    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: str) -> Optional[Task]:
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, task_id: str, data: TaskUpdate) -> Optional[Task]:
        task = await TaskCRUD.get_by_id(db, task_id)
        if not task:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        if data.status == TaskStatus.COMPLETED:
            task.xp_reward = task.calculate_xp()
        await db.flush()
        return task

    @staticmethod
    async def get_tasks_for_date(
        db: AsyncSession, user_id: str, target_date: date
    ) -> list[Task]:
        result = await db.execute(
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.scheduled_date == target_date,
                    Task.status != TaskStatus.CANCELLED,
                )
            )
            .order_by(Task.priority.desc(), Task.scheduled_time.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pending_for_date(
        db: AsyncSession, user_id: str, target_date: date
    ) -> list[Task]:
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.scheduled_date == target_date,
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                )
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_completed(db: AsyncSession, task_id: str, notes: Optional[str] = None) -> Optional[Task]:
        task = await TaskCRUD.get_by_id(db, task_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task.completion_notes = notes
        await db.flush()
        return task

    @staticmethod
    async def mark_missed(db: AsyncSession, task_id: str) -> Optional[Task]:
        task = await TaskCRUD.get_by_id(db, task_id)
        if not task:
            return None
        task.status = TaskStatus.MISSED
        await db.flush()
        return task

    @staticmethod
    async def reschedule(
        db: AsyncSession, task_id: str, new_date: date
    ) -> Optional[Task]:
        task = await TaskCRUD.get_by_id(db, task_id)
        if not task:
            return None
        task.scheduled_date = new_date
        task.status = TaskStatus.RESCHEDULED
        task.reschedule_count += 1
        await db.flush()
        return task

    @staticmethod
    async def auto_reschedule_missed(db: AsyncSession, user_id: str, from_date: date) -> list[Task]:
        """Find missed tasks and reschedule to next available day (avoids overload)."""
        missed = await db.execute(
            select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.scheduled_date == from_date,
                    Task.status == TaskStatus.MISSED,
                )
            )
        )
        missed_tasks = list(missed.scalars().all())
        rescheduled = []

        for task in missed_tasks:
            # Find next day with fewer than 5 tasks
            target = from_date + timedelta(days=1)
            for _ in range(7):  # Look up to 7 days ahead
                count_result = await db.execute(
                    select(func.count(Task.id)).where(
                        and_(
                            Task.user_id == user_id,
                            Task.scheduled_date == target,
                            Task.status != TaskStatus.CANCELLED,
                        )
                    )
                )
                count = count_result.scalar() or 0
                if count < 5:
                    break
                target += timedelta(days=1)

            task.scheduled_date = target
            task.status = TaskStatus.RESCHEDULED
            task.reschedule_count += 1
            rescheduled.append(task)

        await db.flush()
        return rescheduled

    @staticmethod
    async def get_tasks_in_range(
        db: AsyncSession, user_id: str, start: date, end: date
    ) -> list[Task]:
        result = await db.execute(
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.scheduled_date >= start,
                    Task.scheduled_date <= end,
                )
            )
            .order_by(Task.scheduled_date, Task.priority.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_completion_stats(db: AsyncSession, user_id: str, target_date: date) -> dict:
        """Get completion statistics for a specific date."""
        tasks = await TaskCRUD.get_tasks_for_date(db, user_id, target_date)
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        missed = sum(1 for t in tasks if t.status == TaskStatus.MISSED)
        return {
            "total": total,
            "completed": completed,
            "missed": missed,
            "rescheduled": sum(1 for t in tasks if t.status == TaskStatus.RESCHEDULED),
            "pending": sum(1 for t in tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)),
            "rate": completed / total if total > 0 else 0.0,
        }

    @staticmethod
    async def delete(db: AsyncSession, task_id: str) -> bool:
        task = await TaskCRUD.get_by_id(db, task_id)
        if not task:
            return False
        await db.delete(task)
        await db.flush()
        return True
