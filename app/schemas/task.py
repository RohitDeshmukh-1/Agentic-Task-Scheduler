"""Task schemas with full validation."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.task import TaskCategory, TaskDifficulty, TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=1000)
    category: TaskCategory = TaskCategory.OTHER
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    priority: TaskPriority = TaskPriority.MEDIUM
    scheduled_date: date
    scheduled_time: Optional[time] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=480)
    goal_id: Optional[str] = None


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    difficulty: Optional[TaskDifficulty] = None
    priority: Optional[TaskPriority] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    status: Optional[TaskStatus] = None
    completion_notes: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=480)


class TaskBulkUpdate(BaseModel):
    task_ids: List[str]
    status: TaskStatus


class TaskRead(BaseModel):
    id: str
    user_id: str
    goal_id: Optional[str]
    description: str
    category: TaskCategory
    difficulty: TaskDifficulty
    priority: TaskPriority
    scheduled_date: date
    scheduled_time: Optional[time]
    estimated_minutes: Optional[int]
    status: TaskStatus
    reschedule_count: int
    completion_notes: Optional[str]
    xp_reward: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
