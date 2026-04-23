"""Pydantic schemas for request/response validation."""

from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskBulkUpdate
from app.schemas.daily_log import DailyLogRead
from app.schemas.analytics import (
    WeeklyReport,
    ProductivityTrend,
    StreakInfo,
    DashboardStats,
)

__all__ = [
    "UserCreate", "UserRead", "UserUpdate",
    "GoalCreate", "GoalRead", "GoalUpdate",
    "TaskCreate", "TaskRead", "TaskUpdate", "TaskBulkUpdate",
    "DailyLogRead",
    "WeeklyReport", "ProductivityTrend", "StreakInfo", "DashboardStats",
]
