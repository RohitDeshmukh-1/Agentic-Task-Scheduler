"""
Core orchestration service — glues agents, CRUD, and messaging together.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import process_message
from app.crud.conversation import ConversationCRUD, MemoryLogCRUD
from app.crud.daily_log import DailyLogCRUD
from app.crud.goal import GoalCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.models.conversation import ConversationIntent
from app.models.task import TaskCategory, TaskDifficulty, TaskPriority, TaskStatus
from app.schemas.goal import GoalCreate
from app.schemas.task import TaskCreate
from app.services.message_formatter import MessageFormatter
from app.services.telegram import get_telegram_service
from app.core.logging import get_logger

logger = get_logger(__name__)
formatter = MessageFormatter()


class OrchestrationService:
    """Main service that processes incoming messages end-to-end."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.telegram = get_telegram_service()

    async def handle_incoming_message(self, user_id: str, message: str) -> str:
        """Full pipeline: receive message → agent → persist → respond."""

        # 1. Get or create user (user_id is chat_id for Telegram)
        user, is_new = await UserCRUD.get_or_create(self.db, user_id)
        if is_new:
            logger.info("new_user_registered", user_id=user_id)

        # 2. Build user context for agents (includes conversation history)
        user_context = await self._build_user_context(user)

        # 3. Run through LangGraph agent pipeline
        result = await process_message(message, user_context)

        intent = result.get("current_intent", "")
        response = result.get("response", "Something went wrong. Please try again.")
        
        # Map intent string to enum
        intent_enum = self._map_intent_to_enum(intent)

        # 4. Persist based on intent
        if intent == "scheduling":
            tasks = result.get("extracted_tasks", [])
            if tasks:
                await self._persist_tasks(user.id, tasks)
                response = formatter.task_confirmation(tasks)

        elif intent == "status_update":
            mods = result.get("task_modifications", [])
            xp_earned = await self._apply_task_modifications(user, mods)
            if xp_earned > 0:
                old_level = user.level
                await UserCRUD.add_xp(self.db, user, xp_earned)
                leveled_up = user.level > old_level
                streak_msg = formatter.streak_update(
                    user.current_streak, xp_earned, user.level, leveled_up
                )
                response = f"{response}\n\n{streak_msg}"

        elif intent == "goal_setting":
            goal_data = result.get("goal_data")
            if goal_data and goal_data.get("title"):
                goal = await GoalCRUD.create(
                    self.db, user.id,
                    GoalCreate(
                        title=goal_data["title"],
                        description=goal_data.get("description"),
                        target_date=goal_data.get("target_date"),
                        category=goal_data.get("category"),
                    ),
                )
                response = formatter.goal_confirmation(goal_data)

        # 5. Save conversation memory with intent and metadata
        from app.models.conversation import ConversationMemory
        
        summary = response[:100] if response else None
        await ConversationCRUD.save_conversation(
            self.db,
            user_id=user.id,
            role="user",
            content=message,
            intent=intent_enum,
            summary=message[:100],
        )
        await ConversationCRUD.save_conversation(
            self.db,
            user_id=user.id,
            role="assistant",
            content=response,
            intent=intent_enum,
            summary=summary,
        )

        # 6. Reset ignore counter on any interaction
        if user.consecutive_ignores > 0:
            user.consecutive_ignores = 0
            user.dormant_mode = False

        await self.db.flush()

        # 7. Send response
        await self.telegram.send_message(user_id, response)

        return response

    async def _build_user_context(self, user) -> dict:
        """Build the context dict that agents need."""
        today = date.today()
        pending = await TaskCRUD.get_pending_for_date(self.db, user.id, today)
        goals = await GoalCRUD.list_active(self.db, user.id)

        # Get recent completion rate
        week_start = today - timedelta(days=7)
        recent_logs = await DailyLogCRUD.get_range(self.db, user.id, week_start, today)
        rates = [l.completion_rate for l in recent_logs] if recent_logs else [0.0]
        avg_rate = sum(rates) / len(rates)
        
        # Get recent conversation history for LLM context
        conversation_history = await ConversationCRUD.get_recent_conversation(
            self.db, user.id, limit=5
        )
        conversation_context = [
            {"role": conv.role, "content": conv.content} for conv in conversation_history
        ]
        
        # Get recent memory logs for planning context
        memory_summary = await MemoryLogCRUD.get_logs_summary(self.db, user.id, days=7)

        return {
            "user_id": user.id,
            "phone_number": user.phone_number,
            "display_name": user.display_name,
            "timezone": user.timezone,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "consistency_score": user.consistency_score,
            "total_xp": user.total_xp,
            "level": user.level,
            "dormant_mode": user.dormant_mode,
            "pending_tasks_today": [
                {
                    "id": t.id,
                    "description": t.description,
                    "category": t.category.value,
                    "difficulty": t.difficulty.value,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "scheduled_time": str(t.scheduled_time) if t.scheduled_time else None,
                }
                for t in pending
            ],
            "active_goals": [
                {"id": g.id, "title": g.title, "target_date": str(g.target_date) if g.target_date else None}
                for g in goals
            ],
            "recent_completion_rate": avg_rate,
            "conversation_history": conversation_context,
            "memory_logs_summary": memory_summary,
        }

    async def _persist_tasks(self, user_id: str, extracted: list[dict]) -> list:
        """Save extracted tasks to the database."""
        creates = []
        for t in extracted:
            try:
                creates.append(TaskCreate(
                    description=t["description"],
                    category=TaskCategory(t.get("category", "other")),
                    difficulty=TaskDifficulty(t.get("difficulty", "medium")),
                    priority=TaskPriority(t.get("priority", "medium")),
                    scheduled_date=date.fromisoformat(t["scheduled_date"]),
                    scheduled_time=None,
                    estimated_minutes=t.get("estimated_minutes"),
                    goal_id=None,
                ))
            except (ValueError, KeyError) as e:
                logger.warning("task_parse_skip", error=str(e), task=t)
                continue

        return await TaskCRUD.create_many(self.db, user_id, creates)

    async def _apply_task_modifications(self, user, mods: list[dict]) -> int:
        """Apply status changes from tracker agent and return XP earned."""
        xp_earned = 0
        completed_count = 0
        total_count = len(mods)

        for mod in mods:
            task_id = mod.get("task_id")
            if not task_id:
                continue

            status = mod.get("new_status", "completed")

            if status == "completed":
                task = await TaskCRUD.mark_completed(self.db, task_id, mod.get("notes"))
                if task:
                    xp_earned += task.calculate_xp()
                    completed_count += 1
            elif status == "missed":
                await TaskCRUD.mark_missed(self.db, task_id)
            elif status == "rescheduled":
                rd = mod.get("reschedule_date")
                new_date = date.fromisoformat(rd) if rd else date.today() + timedelta(days=1)
                await TaskCRUD.reschedule(self.db, task_id, new_date)

        # Update streak
        all_done = completed_count == total_count and total_count > 0
        await UserCRUD.update_streak(self.db, user, all_done)

        # Update daily log
        today = date.today()
        stats = await TaskCRUD.get_completion_stats(self.db, user.id, today)
        await DailyLogCRUD.upsert(
            self.db, user.id, today,
            total=stats["total"],
            completed=stats["completed"],
            missed=stats["missed"],
            rescheduled=stats["rescheduled"],
            xp=xp_earned,
        )

        return xp_earned

    def _map_intent_to_enum(self, intent_str: str) -> Optional[ConversationIntent]:
        """Map intent string to ConversationIntent enum."""
        intent_mapping = {
            "scheduling": ConversationIntent.SCHEDULING,
            "status_update": ConversationIntent.STATUS_UPDATE,
            "goal_setting": ConversationIntent.GOAL_SETTING,
            "planning": ConversationIntent.PLANNING,
            "analysis": ConversationIntent.ANALYSIS,
            "logging": ConversationIntent.LOGGING,
            "suggestion_request": ConversationIntent.SUGGESTION_REQUEST,
            "query": ConversationIntent.QUERY,
        }
        return intent_mapping.get(intent_str, ConversationIntent.OTHER)
