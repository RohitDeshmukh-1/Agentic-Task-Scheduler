"""
User management and analytics endpoints.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.daily_log import DailyLogCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await UserCRUD.get_all(db)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await UserCRUD.get_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await UserCRUD.get_by_phone(db, data.phone_number)
    if existing:
        raise HTTPException(409, "User already exists")
    return await UserCRUD.create(db, data)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await UserCRUD.update(db, user_id, data)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/{user_id}/analytics")
async def user_analytics(user_id: str, days: int = 30, db: AsyncSession = Depends(get_db)):
    """Get analytics for a user over the last N days."""
    user = await UserCRUD.get_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    end = date.today()
    start = end - timedelta(days=days)
    logs = await DailyLogCRUD.get_range(db, user_id, start, end)
    weekly = await DailyLogCRUD.get_weekly_stats(db, user_id, end)
    consistency = await DailyLogCRUD.get_consistency_score(db, user_id, days)

    return {
        "user_id": user_id,
        "streak": {"current": user.current_streak, "longest": user.longest_streak},
        "level": user.level,
        "total_xp": user.total_xp,
        "consistency_score": consistency,
        "weekly_stats": {
            "total": weekly["total_tasks"],
            "completed": weekly["completed_tasks"],
            "rate": weekly["completion_rate"],
        },
        "daily_trends": [
            {
                "date": str(l.date),
                "total": l.total_tasks,
                "completed": l.completed_tasks,
                "rate": l.completion_rate,
                "xp": l.xp_earned,
            }
            for l in logs
        ],
    }
