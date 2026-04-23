"""User CRUD operations with gamification logic."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserCRUD:

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.phone_number == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create(db: AsyncSession, phone: str) -> tuple[User, bool]:
        """Return (user, created). Auto-registers new users."""
        user = await UserCRUD.get_by_phone(db, phone)
        if user:
            return user, False
        user = User(phone_number=phone)
        db.add(user)
        await db.flush()
        return user, True

    @staticmethod
    async def create(db: AsyncSession, data: UserCreate) -> User:
        user = User(**data.model_dump())
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def update(db: AsyncSession, user_id: str, data: UserUpdate) -> Optional[User]:
        user = await UserCRUD.get_by_id(db, user_id)
        if not user:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await db.flush()
        return user

    @staticmethod
    async def list_active(db: AsyncSession) -> list[User]:
        result = await db.execute(
            select(User).where(User.is_active == True).order_by(User.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_streak(db: AsyncSession, user: User, completed_all: bool) -> User:
        """Update streak based on daily completion. Handles streak break logic."""
        if completed_all:
            user.current_streak += 1
            user.longest_streak = max(user.longest_streak, user.current_streak)
            user.consecutive_ignores = 0
            user.dormant_mode = False
        else:
            user.current_streak = 0

        await db.flush()
        return user

    @staticmethod
    async def add_xp(db: AsyncSession, user: User, xp: int) -> User:
        """Add XP and handle level-up logic."""
        user.total_xp += xp
        # Level formula: level = 1 + total_xp // 100
        new_level = 1 + user.total_xp // 100
        user.level = new_level
        await db.flush()
        return user

    @staticmethod
    async def increment_ignore(db: AsyncSession, user: User) -> User:
        """Track consecutive ignores for dormant mode."""
        user.consecutive_ignores += 1
        if user.consecutive_ignores >= 3:
            user.dormant_mode = True
        await db.flush()
        return user

    @staticmethod
    async def get_all(db: AsyncSession) -> list[User]:
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())
