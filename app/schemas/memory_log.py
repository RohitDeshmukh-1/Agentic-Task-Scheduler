"""Schemas for memory logs and suggestions."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class MemoryLogCreate(BaseModel):
    """Schema for creating a memory log."""
    log_type: str = Field(..., description="Type of log: task_note, plan, reflection, milestone")
    content: str = Field(..., description="The log content")
    category: Optional[str] = Field(None, description="Category for organization")
    importance: int = Field(1, ge=1, le=5, description="Importance level 1-5")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    linked_task_ids: Optional[str] = Field(None, description="Comma-separated task IDs")


class MemoryLogResponse(BaseModel):
    """Schema for memory log response."""
    id: str
    user_id: str
    log_type: str
    content: str
    category: Optional[str]
    importance: int
    tags: Optional[str]
    linked_task_ids: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class LogSummary(BaseModel):
    """Summary of user's recent logs and patterns."""
    total_logs: int
    by_type: dict
    by_category: dict
    recent_high_importance: list


class SuggestionRequest(BaseModel):
    """Request for AI suggestions based on memory and history."""
    suggestion_type: str = Field(
        ..., 
        description="Type of suggestion: planning, optimization, habit_tracking, goal_alignment"
    )
    context_days: int = Field(7, ge=1, le=30, description="Days of history to consider")


class SuggestionResponse(BaseModel):
    """AI-generated suggestions based on user's memory and patterns."""
    suggestion_type: str
    suggestions: list[str] = Field(..., description="List of actionable suggestions")
    reasoning: str = Field(..., description="Why these suggestions are recommended")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    related_logs: list[str] = Field(..., description="Related memory logs that informed suggestions")
