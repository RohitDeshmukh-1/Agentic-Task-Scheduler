"""Goal schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.goal import GoalStatus


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_date: Optional[date] = None
    category: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[GoalStatus] = None
    category: Optional[str] = None


class GoalRead(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    target_date: Optional[date]
    status: GoalStatus
    category: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
