"""User schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$", examples=["+919876543210"])
    display_name: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    preferred_reminder_time: Optional[time] = time(8, 0)
    preferred_check_time: Optional[time] = time(21, 0)


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    timezone: Optional[str] = None
    preferred_reminder_time: Optional[time] = None
    preferred_check_time: Optional[time] = None


class UserRead(BaseModel):
    id: str
    phone_number: str
    display_name: Optional[str]
    timezone: str
    current_streak: int
    longest_streak: int
    consistency_score: float
    total_xp: int
    level: int
    is_active: bool
    dormant_mode: bool
    preferred_reminder_time: Optional[time]
    preferred_check_time: Optional[time]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
