"""ConversationCRUD — queries and manages conversation memory."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationMemory, ConversationIntent, MemoryLog


class ConversationCRUD:
    """CRUD operations for conversation memory."""

    @staticmethod
    async def get_recent_conversation(
        db: AsyncSession, user_id: UUID, limit: int = 10
    ) -> list[ConversationMemory]:
        """Retrieve recent conversation history for a user."""
        stmt = (
            select(ConversationMemory)
            .where(ConversationMemory.user_id == user_id)
            .order_by(desc(ConversationMemory.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()
        return list(reversed(conversations))  # Return in chronological order

    @staticmethod
    async def get_conversation_by_intent(
        db: AsyncSession,
        user_id: UUID,
        intent: ConversationIntent,
        limit: int = 10,
    ) -> list[ConversationMemory]:
        """Retrieve conversations filtered by intent."""
        stmt = (
            select(ConversationMemory)
            .where(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.intent == intent,
                )
            )
            .order_by(desc(ConversationMemory.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_conversation_summary(
        db: AsyncSession, user_id: UUID, days: int = 7
    ) -> dict:
        """Get a summary of recent conversation patterns."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(ConversationMemory)
            .where(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.created_at >= cutoff_date,
                )
            )
            .order_by(ConversationMemory.created_at)
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        # Count intents
        intent_counts = {}
        for conv in conversations:
            if conv.intent:
                intent_str = conv.intent.value
                intent_counts[intent_str] = intent_counts.get(intent_str, 0) + 1

        # Extract planning-related messages
        planning_messages = [
            conv.content
            for conv in conversations
            if conv.role == "user"
            and conv.intent in [ConversationIntent.PLANNING, ConversationIntent.LOGGING]
        ]

        return {
            "total_interactions": len(conversations),
            "intent_distribution": intent_counts,
            "planning_messages": planning_messages,
            "recent_conversations": [
                {"role": conv.role, "content": conv.content} for conv in conversations[-10:]
            ],
        }

    @staticmethod
    async def save_conversation(
        db: AsyncSession,
        user_id: UUID,
        role: str,
        content: str,
        intent: Optional[ConversationIntent] = None,
        summary: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ConversationMemory:
        """Save a conversation entry with metadata."""
        memory = ConversationMemory(
            user_id=user_id,
            role=role,
            content=content,
            intent=intent,
            summary=summary,
            tags=tags,
        )
        db.add(memory)
        return memory

    @staticmethod
    async def get_context_for_lm(
        db: AsyncSession, user_id: UUID, limit: int = 5
    ) -> str:
        """Build context string from recent conversation for LLM."""
        recent = await ConversationCRUD.get_recent_conversation(db, user_id, limit=limit)

        context_lines = ["Recent conversation history:"]
        for conv in recent:
            prefix = "User:" if conv.role == "user" else "Assistant:"
            context_lines.append(f"{prefix} {conv.content}")

        return "\n".join(context_lines)


class MemoryLogCRUD:
    """CRUD operations for personal memory logs."""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: UUID,
        log_type: str,
        content: str,
        category: Optional[str] = None,
        importance: int = 1,
        tags: Optional[str] = None,
        linked_task_ids: Optional[str] = None,
    ) -> MemoryLog:
        """Create a new memory log entry."""
        log = MemoryLog(
            user_id=user_id,
            log_type=log_type,
            content=content,
            category=category,
            importance=importance,
            tags=tags,
            linked_task_ids=linked_task_ids,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_recent_logs(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        log_type: Optional[str] = None,
    ) -> list[MemoryLog]:
        """Retrieve recent memory logs."""
        query = select(MemoryLog).where(MemoryLog.user_id == user_id)

        if log_type:
            query = query.where(MemoryLog.log_type == log_type)

        query = query.order_by(desc(MemoryLog.created_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_logs_by_category(
        db: AsyncSession,
        user_id: UUID,
        category: str,
        limit: int = 10,
    ) -> list[MemoryLog]:
        """Retrieve logs filtered by category."""
        stmt = (
            select(MemoryLog)
            .where(
                and_(
                    MemoryLog.user_id == user_id,
                    MemoryLog.category == category,
                )
            )
            .order_by(desc(MemoryLog.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_logs_summary(
        db: AsyncSession, user_id: UUID, days: int = 7
    ) -> dict:
        """Get summary of recent memory logs and patterns."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(MemoryLog)
            .where(
                and_(
                    MemoryLog.user_id == user_id,
                    MemoryLog.created_at >= cutoff_date,
                )
            )
            .order_by(MemoryLog.created_at)
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()

        # Organize by log type and category
        by_type = {}
        by_category = {}

        for log in logs:
            # By type
            if log.log_type not in by_type:
                by_type[log.log_type] = []
            by_type[log.log_type].append(log.content)

            # By category
            if log.category:
                if log.category not in by_category:
                    by_category[log.category] = []
                by_category[log.category].append(log.content)

        return {
            "total_logs": len(logs),
            "by_type": by_type,
            "by_category": by_category,
            "recent_high_importance": [
                {"type": log.log_type, "content": log.content}
                for log in sorted(logs, key=lambda x: x.importance, reverse=True)[:5]
            ],
        }

    @staticmethod
    async def get_planning_context(
        db: AsyncSession, user_id: UUID, days: int = 7
    ) -> str:
        """Build planning context from recent logs for LLM suggestions."""
        summary = await MemoryLogCRUD.get_logs_summary(db, user_id, days=days)

        context_lines = [
            f"User's recent planning ({days}-day summary):",
            f"Total logs: {summary['total_logs']}",
        ]

        # Add by type
        for log_type, contents in summary["by_type"].items():
            context_lines.append(f"\n{log_type.upper()} ({len(contents)} entries):")
            for content in contents[:3]:  # Show top 3 per type
                context_lines.append(f"  - {content[:100]}")

        # Add by category
        if summary["by_category"]:
            context_lines.append("\nBy Category:")
            for category, contents in summary["by_category"].items():
                context_lines.append(f"  {category}: {len(contents)} entries")

        return "\n".join(context_lines)
