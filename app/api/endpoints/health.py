"""
Health check and system info endpoints.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    try:
        # Timeout the DB check so it doesn't hang the healthcheck
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=3.0)
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/config/public")
async def public_config():
    """Non-sensitive configuration for the dashboard."""
    return {
        "app_name": settings.app_name,
        "messaging_platform": "telegram",
        "telegram_mode": settings.telegram_mode,
        "database_is_sqlite": settings.is_sqlite,
        "scheduler": {
            "morning_reminder": f"{settings.morning_reminder_hour:02d}:{settings.morning_reminder_minute:02d}",
            "night_check": f"{settings.night_check_hour:02d}:{settings.night_check_minute:02d}",
            "weekly_report": f"{settings.weekly_report_day} at {settings.weekly_report_hour:02d}:00",
        },
        "dashboard_enabled": settings.dashboard_enabled,
    }
