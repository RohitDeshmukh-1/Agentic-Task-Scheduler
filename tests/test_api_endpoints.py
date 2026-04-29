"""
API endpoint tests for deployment-critical Telegram and health paths.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints.health import get_db as health_get_db
from app.api.endpoints.webhook import get_db as webhook_get_db
from app.main import app
from app.services.orchestrator import OrchestrationService
from app.services.telegram import TelegramService


@pytest.mark.asyncio
async def test_health_endpoint_returns_healthy(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[health_get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["app"] == "TaskPilot"
    finally:
        app.dependency_overrides.pop(health_get_db, None)


@pytest.mark.asyncio
async def test_telegram_webhook_message(monkeypatch, db: AsyncSession):
    async def override_get_db():
        yield db

    async def fake_handle(self, user_id: str, message: str) -> str:
        assert user_id == "123456"
        assert message == "hello"
        return "ok"

    monkeypatch.setattr(OrchestrationService, "handle_incoming_message", fake_handle)
    app.dependency_overrides[webhook_get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhook/telegram",
                headers={"X-Telegram-Bot-Api-Secret-Token": "taskpilot_telegram_2026"},
                json={
                    "message": {
                        "chat": {"id": 123456},
                        "from": {"id": 123456},
                        "text": "hello",
                    }
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "processed"
        assert payload["response_preview"] == "ok"
    finally:
        app.dependency_overrides.pop(webhook_get_db, None)


@pytest.mark.asyncio
async def test_telegram_webhook_callback(monkeypatch, db: AsyncSession):
    async def override_get_db():
        yield db

    async def fake_handle(self, user_id: str, message: str) -> str:
        assert user_id == "999"
        assert message == "/complete_task"
        return "done"

    async def fake_answer(self, callback_query_id: str, text: str = "", show_alert: bool = False) -> bool:
        assert callback_query_id == "cb-1"
        return True

    monkeypatch.setattr(OrchestrationService, "handle_incoming_message", fake_handle)
    monkeypatch.setattr(TelegramService, "answer_callback_query", fake_answer)
    app.dependency_overrides[webhook_get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhook/telegram",
                headers={"X-Telegram-Bot-Api-Secret-Token": "taskpilot_telegram_2026"},
                json={
                    "callback_query": {
                        "id": "cb-1",
                        "message": {"chat": {"id": 999}},
                        "data": "complete_task",
                    }
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "processed"
        assert payload["callback_id"] == "cb-1"
    finally:
        app.dependency_overrides.pop(webhook_get_db, None)
