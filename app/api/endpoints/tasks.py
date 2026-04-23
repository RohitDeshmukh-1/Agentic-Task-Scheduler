"""
Task management REST endpoints for the dashboard.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.task import TaskCRUD
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[TaskRead])
async def list_tasks(
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """List tasks for a user within a date range."""
    start = start_date or date.today()
    end = end_date or start
    tasks = await TaskCRUD.get_tasks_in_range(db, user_id, start, end)
    return tasks


@router.get("/today", response_model=list[TaskRead])
async def today_tasks(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all tasks for today."""
    return await TaskCRUD.get_tasks_for_date(db, user_id, date.today())


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    user_id: str, data: TaskCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    return await TaskCRUD.create(db, user_id, data)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str, data: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    task = await TaskCRUD.update(db, task_id, data)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Mark a task as completed."""
    task = await TaskCRUD.mark_completed(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    success = await TaskCRUD.delete(db, task_id)
    if not success:
        raise HTTPException(404, "Task not found")


@router.get("/stats")
async def task_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get completion stats for today."""
    return await TaskCRUD.get_completion_stats(db, user_id, date.today())
