"""Tests for conversation memory and memory logs."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.conversation import ConversationCRUD, MemoryLogCRUD
from app.crud.user import UserCRUD
from app.models.conversation import ConversationIntent, ConversationMemory, MemoryLog


@pytest.mark.asyncio
async def test_save_conversation(db: AsyncSession):
    """Test saving conversation with metadata."""
    # Create user
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Save conversation
    memory = await ConversationCRUD.save_conversation(
        db,
        user_id=user.id,
        role="user",
        content="Add task: finish project report",
        intent=ConversationIntent.SCHEDULING,
        summary="User wants to schedule task",
        tags="task, work",
    )

    assert memory.role == "user"
    assert memory.intent == ConversationIntent.SCHEDULING
    assert memory.tags == "task, work"

    await db.commit()


@pytest.mark.asyncio
async def test_get_recent_conversation(db: AsyncSession):
    """Test retrieving recent conversation history."""
    # Create user
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Save multiple conversations
    for i in range(5):
        await ConversationCRUD.save_conversation(
            db,
            user_id=user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            intent=ConversationIntent.SCHEDULING,
        )

    await db.commit()

    # Retrieve recent
    recent = await ConversationCRUD.get_recent_conversation(db, user.id, limit=3)

    assert len(recent) == 3
    assert recent[0].content == "Message 2"  # Oldest first (chronological)
    assert recent[2].content == "Message 4"  # Newest last


@pytest.mark.asyncio
async def test_get_conversation_by_intent(db: AsyncSession):
    """Test filtering conversations by intent."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Save conversations with different intents
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Add task", ConversationIntent.SCHEDULING
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Completed task", ConversationIntent.STATUS_UPDATE
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Set goal", ConversationIntent.GOAL_SETTING
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Add task 2", ConversationIntent.SCHEDULING
    )

    await db.commit()

    # Get scheduling intents
    scheduling = await ConversationCRUD.get_conversation_by_intent(
        db, user.id, ConversationIntent.SCHEDULING
    )

    assert len(scheduling) == 2
    assert all(m.intent == ConversationIntent.SCHEDULING for m in scheduling)


@pytest.mark.asyncio
async def test_get_conversation_summary(db: AsyncSession):
    """Test conversation summary generation."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Save conversations
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Plan my week", ConversationIntent.PLANNING
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "assistant", "Here's a plan", ConversationIntent.PLANNING
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "Add 3 tasks", ConversationIntent.SCHEDULING
    )

    await db.commit()

    summary = await ConversationCRUD.get_conversation_summary(db, user.id, days=7)

    assert summary["total_interactions"] >= 3
    assert "intent_distribution" in summary
    assert "planning_messages" in summary
    assert "Plan my week" in summary["planning_messages"]


@pytest.mark.asyncio
async def test_create_memory_log(db: AsyncSession):
    """Test creating a memory log."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    log = await MemoryLogCRUD.create(
        db,
        user_id=user.id,
        log_type="task_note",
        content="Finished early today, planning to add more tasks tomorrow",
        category="productivity",
        importance=4,
        tags="productive,momentum",
        linked_task_ids="123,456",
    )

    assert log.log_type == "task_note"
    assert log.importance == 4
    assert log.category == "productivity"

    await db.commit()


@pytest.mark.asyncio
async def test_get_recent_logs(db: AsyncSession):
    """Test retrieving recent memory logs."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Create multiple logs
    for i in range(5):
        await MemoryLogCRUD.create(
            db,
            user_id=user.id,
            log_type="task_note" if i % 2 == 0 else "reflection",
            content=f"Log entry {i}",
            category="general",
        )

    await db.commit()

    recent = await MemoryLogCRUD.get_recent_logs(db, user.id, limit=3)

    assert len(recent) == 3
    assert recent[0].content == "Log entry 4"  # Most recent first


@pytest.mark.asyncio
async def test_get_logs_by_category(db: AsyncSession):
    """Test filtering logs by category."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    categories = ["work", "health", "work", "personal"]
    for i, cat in enumerate(categories):
        await MemoryLogCRUD.create(
            db,
            user_id=user.id,
            log_type="task_note",
            content=f"Entry in {cat}",
            category=cat,
        )

    await db.commit()

    work_logs = await MemoryLogCRUD.get_logs_by_category(db, user.id, "work")

    assert len(work_logs) == 2
    assert all(log.category == "work" for log in work_logs)


@pytest.mark.asyncio
async def test_get_logs_summary(db: AsyncSession):
    """Test memory logs summary generation."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Create logs with different types and categories
    await MemoryLogCRUD.create(
        db, user.id, "task_note", "Finished task", "work", importance=3
    )
    await MemoryLogCRUD.create(
        db, user.id, "reflection", "Good day", "personal", importance=5
    )
    await MemoryLogCRUD.create(
        db, user.id, "plan", "Plan tomorrow", "work", importance=4
    )

    await db.commit()

    summary = await MemoryLogCRUD.get_logs_summary(db, user.id, days=7)

    assert summary["total_logs"] == 3
    assert "by_type" in summary
    assert "by_category" in summary
    assert "task_note" in summary["by_type"]
    assert "work" in summary["by_category"]
    assert len(summary["recent_high_importance"]) > 0


@pytest.mark.asyncio
async def test_get_context_for_lm(db: AsyncSession):
    """Test building LLM context from conversations."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Save conversation
    await ConversationCRUD.save_conversation(
        db, user.id, "user", "I want to focus on health this week"
    )
    await ConversationCRUD.save_conversation(
        db, user.id, "assistant", "Great! Let's build a health-focused plan"
    )

    await db.commit()

    context = await ConversationCRUD.get_context_for_lm(db, user.id)

    assert "Recent conversation history:" in context
    assert "User:" in context
    assert "Assistant:" in context
    assert "health" in context


@pytest.mark.asyncio
async def test_get_planning_context(db: AsyncSession):
    """Test building planning context from memory logs."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    # Create planning logs
    await MemoryLogCRUD.create(
        db, user.id, "plan", "Focus on project X", "work", importance=5
    )
    await MemoryLogCRUD.create(
        db, user.id, "reflection", "Stayed consistent", "health", importance=4
    )

    await db.commit()

    context = await MemoryLogCRUD.get_planning_context(db, user.id, days=7)

    assert "planning" in context.lower() or "summary" in context.lower()
    assert "Total logs:" in context or "total logs" in context.lower()


@pytest.mark.asyncio
async def test_memory_log_linked_tasks(db: AsyncSession):
    """Test memory log with linked task IDs."""
    user, _ = await UserCRUD.get_or_create(db, "1234567890")

    log = await MemoryLogCRUD.create(
        db,
        user_id=user.id,
        log_type="task_note",
        content="Completed related tasks",
        linked_task_ids="uuid1,uuid2,uuid3",
    )

    assert log.linked_task_ids == "uuid1,uuid2,uuid3"

    await db.commit()
