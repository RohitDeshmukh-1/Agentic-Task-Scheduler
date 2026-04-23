"""Goal CRUD operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalStatus
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalCRUD:

    @staticmethod
    async def create(db: AsyncSession, user_id: str, data: GoalCreate) -> Goal:
        goal = Goal(user_id=user_id, **data.model_dump())
        db.add(goal)
        await db.flush()
        return goal

    @staticmethod
    async def get_by_id(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        result = await db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, goal_id: str, data: GoalUpdate) -> Optional[Goal]:
        goal = await GoalCRUD.get_by_id(db, goal_id)
        if not goal:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        await db.flush()
        return goal

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: str,
        status: Optional[GoalStatus] = None,
    ) -> list[Goal]:
        query = select(Goal).where(Goal.user_id == user_id)
        if status:
            query = query.where(Goal.status == status)
        query = query.order_by(Goal.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_active(db: AsyncSession, user_id: str) -> list[Goal]:
        return await GoalCRUD.list_by_user(db, user_id, GoalStatus.ACTIVE)

    @staticmethod
    async def delete(db: AsyncSession, goal_id: str) -> bool:
        goal = await GoalCRUD.get_by_id(db, goal_id)
        if not goal:
            return False
        await db.delete(goal)
        await db.flush()
        return True
