"""
Bot flow tests covering scheduling, goal creation, and reminder delivery.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.agents import graph as graph_module
from app.crud.goal import GoalCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.models.goal import Goal
from app.models.task import TaskStatus
import app.services.orchestrator as orchestrator_module
from app.services import scheduler as scheduler_module
from app.services.scheduler import morning_reminder_job
from app.services.telegram import TelegramService


class FakeTelegram:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        self.sent.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )
        return True


@pytest.mark.asyncio
async def test_orchestration_schedules_tasks(db, monkeypatch):
    fake_telegram = FakeTelegram()

    async def fake_process_message(message: str, user_context: dict):
        assert message == "Add a task for tomorrow"
        assert user_context["user_id"] is not None
        return {
            "current_intent": "scheduling",
            "extracted_tasks": [
                {
                    "description": "Call the bank",
                    "category": "other",
                    "difficulty": "medium",
                    "priority": "high",
                    "scheduled_date": date.today().isoformat(),
                    "estimated_minutes": 15,
                }
            ],
            "response": "ignored by scheduling branch",
        }

    monkeypatch.setattr(orchestrator_module, "process_message", fake_process_message)
    monkeypatch.setattr(orchestrator_module, "get_telegram_service", lambda: fake_telegram)

    service = orchestrator_module.OrchestrationService(db)
    response = await service.handle_incoming_message("123456", "Add a task for tomorrow")

    user = await UserCRUD.get_by_phone(db, "123456")
    assert user is not None
    tasks = await TaskCRUD.get_tasks_for_date(db, user.id, date.today())
    assert len(tasks) == 1
    assert tasks[0].description == "Call the bank"
    assert tasks[0].status == TaskStatus.PENDING
    assert "Tasks scheduled" in response
    assert fake_telegram.sent[0]["chat_id"] == "123456"
    assert "Tasks scheduled" in fake_telegram.sent[0]["text"]


@pytest.mark.asyncio
async def test_orchestration_creates_goal(db, monkeypatch):
    fake_telegram = FakeTelegram()

    async def fake_process_message(message: str, user_context: dict):
        assert message == "Set a goal to read 12 books"
        return {
            "current_intent": "goal_setting",
            "goal_data": {
                "title": "Read 12 books",
                "description": "Finish one book per month",
                "target_date": date.today().isoformat(),
                "category": "personal",
                "response": "Goal set!",
            },
            "response": "Goal set!",
        }

    monkeypatch.setattr(orchestrator_module, "process_message", fake_process_message)
    monkeypatch.setattr(orchestrator_module, "get_telegram_service", lambda: fake_telegram)

    service = orchestrator_module.OrchestrationService(db)
    response = await service.handle_incoming_message("654321", "Set a goal to read 12 books")

    user = await UserCRUD.get_by_phone(db, "654321")
    assert user is not None
    result = await db.execute(select(Goal).where(Goal.user_id == user.id))
    goals = list(result.scalars().all())

    assert len(goals) == 1
    assert goals[0].title == "Read 12 books"
    assert goals[0].description == "Finish one book per month"
    assert "Goal Set" in response
    assert fake_telegram.sent[0]["chat_id"] == "654321"
    assert "Goal Set" in fake_telegram.sent[0]["text"]


@pytest.mark.asyncio
async def test_morning_reminder_job_sends_task_summary(monkeypatch):
    fake_telegram = FakeTelegram()
    user = SimpleNamespace(
        phone_number="999111",
        display_name="Rohit",
        current_streak=4,
        level=2,
        total_xp=180,
        dormant_mode=False,
        id="user-1",
    )
    task = SimpleNamespace(
        description="Pay rent",
        priority=SimpleNamespace(value="high"),
        difficulty=SimpleNamespace(value="medium"),
        scheduled_time=None,
    )

    class DummyContext:
        async def __aenter__(self):
            async def commit():
                return None

            return SimpleNamespace(commit=commit)

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def fake_list_active(db):
        return [user]

    async def fake_get_tasks_for_date(db, user_id, target_date):
        assert user_id == user.id
        return [task]

    monkeypatch.setattr(scheduler_module, "get_telegram_service", lambda: fake_telegram)
    monkeypatch.setattr(scheduler_module.UserCRUD, "list_active", fake_list_active)
    monkeypatch.setattr(scheduler_module.TaskCRUD, "get_tasks_for_date", fake_get_tasks_for_date)
    monkeypatch.setattr(scheduler_module, "async_session_factory", lambda: DummyContext())

    await morning_reminder_job()

    assert len(fake_telegram.sent) == 1
    sent = fake_telegram.sent[0]
    assert sent["chat_id"] == user.phone_number
    assert "Good Morning" in sent["text"]
    assert "Pay rent" in sent["text"]