"""Analytics schemas for dashboards and weekly reports."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel


class StreakInfo(BaseModel):
    current: int
    longest: int
    is_at_risk: bool  # True if yesterday was missed


class ProductivityTrend(BaseModel):
    date: date
    completion_rate: float
    total_tasks: int
    completed_tasks: int
    xp_earned: int


class CategoryBreakdown(BaseModel):
    category: str
    total: int
    completed: int
    rate: float


class WeeklyReport(BaseModel):
    user_id: str
    week_start: date
    week_end: date
    total_tasks: int
    completed_tasks: int
    missed_tasks: int
    rescheduled_tasks: int
    overall_completion_rate: float
    xp_earned: int
    streak: StreakInfo
    daily_trends: List[ProductivityTrend]
    category_breakdown: List[CategoryBreakdown]
    insights: List[str]  # AI-generated insights
    best_day: Optional[str] = None
    worst_day: Optional[str] = None


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_tasks_today: int
    completed_tasks_today: int
    completion_rate_today: float
    total_tasks_week: int
    completed_tasks_week: int
    top_categories: Dict[str, int]
    streak_distribution: Dict[str, int]
