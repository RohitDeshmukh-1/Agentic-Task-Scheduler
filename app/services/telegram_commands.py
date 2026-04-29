"""
Telegram command handlers for memory logging and suggestions.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.conversation import MemoryLogCRUD
from app.crud.user import UserCRUD
from app.services.message_formatter import MessageFormatter
from app.services.telegram import get_telegram_service
from app.core.logging import get_logger

logger = get_logger(__name__)
formatter = MessageFormatter()


async def handle_log_command(
    chat_id: str, message_text: str, db: AsyncSession
) -> str:
    """
    Handle /log command for users to log tasks and plans.
    Format: /log <type> <category> <content>
    Example: /log task work Completed project report on time
    """
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)

        parts = message_text.split(" ", 3)
        if len(parts) < 3:
            return (
                "Usage: /log <type> <category> <content>\n"
                "Types: task_note, plan, reflection, milestone\n"
                "Example: /log task_note work Finished the report early today"
            )

        log_type = parts[1]
        category = parts[2]
        content = parts[3] if len(parts) > 3 else ""

        valid_types = ["task_note", "plan", "reflection", "milestone"]
        if log_type not in valid_types:
            return f"Invalid log type. Valid types: {', '.join(valid_types)}"

        if not content:
            return "Please provide log content"

        # Create memory log
        log = await MemoryLogCRUD.create(
            db,
            user_id=user.id,
            log_type=log_type,
            content=content,
            category=category,
            importance=1,
        )

        await db.commit()
        logger.info("memory_log_created_via_telegram", user_id=user.id, log_type=log_type)

        return f"✅ Logged {log_type} in {category}:\n{content}"

    except Exception as e:
        logger.error("log_command_failed", error=str(e))
        return "Failed to log entry. Please try again."


async def handle_memory_command(
    chat_id: str, db: AsyncSession
) -> str:
    """
    Handle /memory command to show recent memory logs summary.
    """
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)

        summary = await MemoryLogCRUD.get_logs_summary(db, user.id, days=7)

        lines = ["📝 Your Memory Log Summary (Last 7 Days)\n"]
        lines.append(f"Total logs: {summary['total_logs']}")

        # By type
        if summary["by_type"]:
            lines.append("\n📋 By Type:")
            for log_type, contents in summary["by_type"].items():
                lines.append(f"  • {log_type}: {len(contents)} entries")

        # By category
        if summary["by_category"]:
            lines.append("\n📂 By Category:")
            for category, contents in summary["by_category"].items():
                lines.append(f"  • {category}: {len(contents)} entries")

        # High importance
        if summary["recent_high_importance"]:
            lines.append("\n⭐ Recent High Importance:")
            for item in summary["recent_high_importance"][:3]:
                lines.append(f"  • {item['type']}: {item['content'][:50]}")

        return "\n".join(lines)

    except Exception as e:
        logger.error("memory_command_failed", error=str(e))
        return "Failed to retrieve memory summary. Please try again."


async def handle_suggest_command(
    chat_id: str, db: AsyncSession
) -> str:
    """
    Handle /suggest command to get AI suggestions based on memory and history.
    """
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)

        # Get planning context
        from app.crud.conversation import ConversationCRUD

        planning_context = await MemoryLogCRUD.get_planning_context(db, user.id, days=7)
        conversation_context = await ConversationCRUD.get_context_for_lm(db, user.id, limit=5)

        # Build suggestion prompt
        suggestion_prompt = f"""
Based on the user's recent memory logs and conversation history, provide 3-5 specific, actionable suggestions to help them improve their task planning and productivity.

Memory Context:
{planning_context}

Conversation Context:
{conversation_context}

User Level: {user.level}
Current Streak: {user.current_streak} days
XP: {user.total_xp}

Provide practical suggestions they can implement today or this week.
"""

        # Call LLM for suggestions
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

        response_text = result.get("response", "No suggestions available right now")

        logger.info("suggestions_generated_via_telegram", user_id=user.id)

        return f"💡 Personalized Suggestions:\n\n{response_text}"

    except Exception as e:
        logger.error("suggest_command_failed", error=str(e))
        return "Failed to generate suggestions. Please try again."


async def handle_reflect_command(
    chat_id: str, message_text: str, db: AsyncSession
) -> str:
    """
    Handle /reflect command for users to add reflection/journal entries.
    Format: /reflect <content>
    """
    try:
        user, _ = await UserCRUD.get_or_create(db, chat_id)

        content = message_text.replace("/reflect", "", 1).strip()

        if not content:
            return "Please provide your reflection.\nExample: /reflect Today was productive, completed 5 tasks and learned something new"

        # Create reflection log
        log = await MemoryLogCRUD.create(
            db,
            user_id=user.id,
            log_type="reflection",
            content=content,
            category="personal",
            importance=2,
        )

        await db.commit()
        logger.info("reflection_logged_via_telegram", user_id=user.id)

        return f"✨ Reflection logged:\n{content}\n\nKeep reflecting to understand your patterns better!"

    except Exception as e:
        logger.error("reflect_command_failed", error=str(e))
        return "Failed to save reflection. Please try again."


async def process_telegram_command(
    chat_id: str, text: str, db: AsyncSession
) -> str:
    """Route Telegram commands to appropriate handlers."""
    if text.startswith("/log"):
        return await handle_log_command(chat_id, text, db)
    elif text.startswith("/memory"):
        return await handle_memory_command(chat_id, db)
    elif text.startswith("/suggest"):
        return await handle_suggest_command(chat_id, db)
    elif text.startswith("/reflect"):
        return await handle_reflect_command(chat_id, text, db)
    else:
        return None


# Command descriptions for Telegram
TELEGRAM_COMMANDS = [
    {"command": "log", "description": "Log a task, plan, reflection, or milestone. Format: /log <type> <category> <content>"},
    {"command": "memory", "description": "View your 7-day memory log summary"},
    {"command": "suggest", "description": "Get AI suggestions based on your recent activity and plans"},
    {"command": "reflect", "description": "Add a personal reflection or journal entry"},
]
