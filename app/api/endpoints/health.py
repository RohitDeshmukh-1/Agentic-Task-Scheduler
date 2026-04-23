"""
Health check and system info endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
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
        "whatsapp_mode": settings.whatsapp_mode,
        "scheduler": {
            "morning_reminder": f"{settings.morning_reminder_hour:02d}:{settings.morning_reminder_minute:02d}",
            "night_check": f"{settings.night_check_hour:02d}:{settings.night_check_minute:02d}",
            "weekly_report": f"{settings.weekly_report_day} at {settings.weekly_report_hour:02d}:00",
        },
        "dashboard_enabled": settings.dashboard_enabled,
    }
