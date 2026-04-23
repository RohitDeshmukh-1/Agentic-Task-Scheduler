"""
Unit tests for CRUD operations.
"""

from datetime import date, timedelta

import pytest
import pytest_asyncio

from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_user(db):
    user = await UserCRUD.create(db, UserCreate(phone_number="+919876543210"))
    await db.flush()
    assert user.id is not None
    assert user.phone_number == "+919876543210"
    assert user.current_streak == 0
    assert user.level == 1


@pytest.mark.asyncio
async def test_get_or_create_user(db):
    user1, created1 = await UserCRUD.get_or_create(db, "+911111111111")
    await db.flush()
    assert created1 is True

    user2, created2 = await UserCRUD.get_or_create(db, "+911111111111")
    assert created2 is False
    assert user1.id == user2.id


@pytest.mark.asyncio
async def test_streak_logic(db):
    user, _ = await UserCRUD.get_or_create(db, "+912222222222")
    await db.flush()

    # Complete all tasks — streak should increase
    await UserCRUD.update_streak(db, user, completed_all=True)
    assert user.current_streak == 1

    await UserCRUD.update_streak(db, user, completed_all=True)
    assert user.current_streak == 2
    assert user.longest_streak == 2

    # Break streak
    await UserCRUD.update_streak(db, user, completed_all=False)
    assert user.current_streak == 0
    assert user.longest_streak == 2  # Longest preserved


@pytest.mark.asyncio
async def test_xp_and_level(db):
    user, _ = await UserCRUD.get_or_create(db, "+913333333333")
    await db.flush()

    await UserCRUD.add_xp(db, user, 50)
    assert user.total_xp == 50
    assert user.level == 1  # 1 + 50//100 = 1

    await UserCRUD.add_xp(db, user, 60)
    assert user.total_xp == 110
    assert user.level == 2  # 1 + 110//100 = 2


@pytest.mark.asyncio
async def test_dormant_mode(db):
    user, _ = await UserCRUD.get_or_create(db, "+914444444444")
    await db.flush()

    for _ in range(3):
        await UserCRUD.increment_ignore(db, user)

    assert user.consecutive_ignores == 3
    assert user.dormant_mode is True


@pytest.mark.asyncio
async def test_create_task(db):
    user, _ = await UserCRUD.get_or_create(db, "+915555555555")
    await db.flush()

    task = await TaskCRUD.create(
        db, user.id,
        TaskCreate(
            description="Call the bank",
            scheduled_date=date.today(),
        ),
    )
    await db.flush()

    assert task.id is not None
    assert task.description == "Call the bank"
    assert task.status == TaskStatus.PENDING
    assert task.xp_reward > 0


@pytest.mark.asyncio
async def test_task_completion(db):
    user, _ = await UserCRUD.get_or_create(db, "+916666666666")
    await db.flush()

    task = await TaskCRUD.create(
        db, user.id,
        TaskCreate(description="Study math", scheduled_date=date.today()),
    )
    await db.flush()

    completed = await TaskCRUD.mark_completed(db, task.id, notes="Done!")
    assert completed.status == TaskStatus.COMPLETED
    assert completed.completion_notes == "Done!"


@pytest.mark.asyncio
async def test_task_reschedule(db):
    user, _ = await UserCRUD.get_or_create(db, "+917777777777")
    await db.flush()

    task = await TaskCRUD.create(
        db, user.id,
        TaskCreate(description="Go jogging", scheduled_date=date.today()),
    )
    await db.flush()

    tomorrow = date.today() + timedelta(days=1)
    rescheduled = await TaskCRUD.reschedule(db, task.id, tomorrow)
    assert rescheduled.scheduled_date == tomorrow
    assert rescheduled.status == TaskStatus.RESCHEDULED
    assert rescheduled.reschedule_count == 1


@pytest.mark.asyncio
async def test_completion_stats(db):
    user, _ = await UserCRUD.get_or_create(db, "+918888888888")
    await db.flush()
    today = date.today()

    await TaskCRUD.create(db, user.id, TaskCreate(description="T1", scheduled_date=today))
    await TaskCRUD.create(db, user.id, TaskCreate(description="T2", scheduled_date=today))
    t3 = await TaskCRUD.create(db, user.id, TaskCreate(description="T3", scheduled_date=today))
    await db.flush()

    await TaskCRUD.mark_completed(db, t3.id)
    stats = await TaskCRUD.get_completion_stats(db, user.id, today)

    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["pending"] == 2
    assert abs(stats["rate"] - 1/3) < 0.01
