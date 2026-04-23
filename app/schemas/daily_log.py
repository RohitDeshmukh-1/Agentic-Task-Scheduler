"""DailyLog schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class DailyLogRead(BaseModel):
    id: str
    user_id: str
    date: date
    total_tasks: int
    completed_tasks: int
    missed_tasks: int
    rescheduled_tasks: int
    completion_rate: float
    xp_earned: int
    mood: str
    created_at: datetime

    model_config = {"from_attributes": True}
