"""CRUD operations for all domain entities."""

from app.crud.user import UserCRUD
from app.crud.goal import GoalCRUD
from app.crud.task import TaskCRUD
from app.crud.daily_log import DailyLogCRUD

__all__ = ["UserCRUD", "GoalCRUD", "TaskCRUD", "DailyLogCRUD"]
