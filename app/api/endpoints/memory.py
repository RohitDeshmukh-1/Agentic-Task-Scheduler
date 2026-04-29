"""API endpoints for memory logs and suggestions."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.core.database import get_db
from app.crud.conversation import MemoryLogCRUD, ConversationCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.schemas.memory_log import (
    MemoryLogCreate,
    MemoryLogResponse,
    LogSummary,
    SuggestionRequest,
    SuggestionResponse,
)
from app.services.telegram import get_telegram_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.post("/log", response_model=MemoryLogResponse)
async def create_memory_log(
    chat_id: str,  # Telegram chat_id
    log_data: MemoryLogCreate,
    db: AsyncSession = Depends(get_db),
) -> MemoryLogResponse:
    """Create a memory log entry."""
    try:
        # Get user by chat_id
        user, _ = await UserCRUD.get_or_create(db, chat_id)

        # Create log
        memory_log = await MemoryLogCRUD.create(
            db,
            user_id=user.id,
            log_type=log_data.log_type,
            content=log_data.content,
            category=log_data.category,
            importance=log_data.importance,
            tags=log_data.tags,
            linked_task_ids=log_data.linked_task_ids,
        )

        await db.commit()
        logger.info("memory_log_created", user_id=user.id, log_type=log_data.log_type)

        return MemoryLogResponse.model_validate(memory_log)

    except Exception as e:
        await db.rollback()
        logger.error("memory_log_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create memory log")


@router.get("/logs", response_model=list[MemoryLogResponse])
async def get_recent_logs(
    chat_id: str,
    limit: int = 10,
    log_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[MemoryLogResponse]:
    """Retrieve recent memory logs."""
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)
        logs = await MemoryLogCRUD.get_recent_logs(
            db, user_id=user.id, limit=limit, log_type=log_type
        )

        return [MemoryLogResponse.model_validate(log) for log in logs]

    except Exception as e:
        logger.error("memory_log_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve memory logs")


@router.get("/summary", response_model=LogSummary)
async def get_logs_summary(
    chat_id: str,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
) -> LogSummary:
    """Get summary of recent memory logs."""
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)
        summary = await MemoryLogCRUD.get_logs_summary(db, user_id=user.id, days=days)

        return LogSummary(**summary)

    except Exception as e:
        logger.error("memory_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.post("/suggest", response_model=SuggestionResponse)
async def get_suggestions(
    chat_id: str,
    request: SuggestionRequest,
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    """Generate AI suggestions based on user's memory logs and conversation history."""
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)
        telegram = get_telegram_service()

        # Gather context
        memory_context = await MemoryLogCRUD.get_planning_context(
            db, user_id=user.id, days=request.context_days
        )
        conversation_context = await ConversationCRUD.get_context_for_lm(
            db, user_id=user.id, limit=5
        )
        
        # Get pending tasks for context
        pending_tasks = await TaskCRUD.get_pending_for_date(db, user.id)
        task_context = f"Pending tasks: {len(pending_tasks)} tasks"
        if pending_tasks:
            task_lines = [
                f"- {task.title} (priority: {task.priority.value})" for task in pending_tasks[:5]
            ]
            task_context += "\n" + "\n".join(task_lines)

        # Build prompt for LLM
        suggestion_prompt = f"""
Based on the user's memory logs, conversation history, and current tasks, provide {request.suggestion_type} suggestions:

{memory_context}

{conversation_context}

{task_context}

Generate 3-5 actionable, specific suggestions. Consider patterns in their planning, past goals, and behavior.
"""

        # Call LLM for suggestions (using Groq via existing agent framework)
        from app.agents.graph import process_message

        result = await process_message(
            suggestion_prompt,
            {
                "user_name": user.display_name or "User",
                "user_stats": {
                    "level": user.level,
                    "streak": user.current_streak,
                    "xp": user.total_xp,
                },
            }
        )

        response_text = result.get("response", "Could not generate suggestions")

        # Extract relevant logs
        recent_logs = await MemoryLogCRUD.get_recent_logs(db, user_id=user.id, limit=5)
        related_logs = [log.content[:100] for log in recent_logs]

        logger.info(
            "suggestions_generated",
            user_id=user.id,
            suggestion_type=request.suggestion_type,
        )

        return SuggestionResponse(
            suggestion_type=request.suggestion_type,
            suggestions=[
                s.strip() for s in response_text.split("\n") if s.strip()
            ][:5],
            reasoning="Based on your recent planning, conversation history, and task patterns",
            confidence=0.8,
            related_logs=related_logs,
        )

    except Exception as e:
        logger.error("suggestion_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")
