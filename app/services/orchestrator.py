"""
Core orchestration service — glues agents, CRUD, and messaging together.
"""

from __future__ import annotations

from datetime import date, time, timedelta
import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import process_message
from app.crud.conversation import ConversationCRUD, MemoryLogCRUD
from app.crud.daily_log import DailyLogCRUD
from app.crud.goal import GoalCRUD
from app.crud.recurring_task import RecurringTaskCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.models.conversation import ConversationIntent
from app.models.recurring_task import RecurrenceFrequency
from app.models.task import TaskCategory, TaskDifficulty, TaskPriority, TaskStatus
from app.schemas.goal import GoalCreate
from app.schemas.task import TaskCreate
from app.config import get_settings
from app.services.message_formatter import MessageFormatter
from app.services.telegram import get_telegram_service
from app.core.logging import get_logger

logger = get_logger(__name__)
formatter = MessageFormatter()
settings = get_settings()

# Per-user in-memory state for multi-turn conversations.
# Keyed by Telegram chat_id (str) — each user gets their own isolated slot.
# This is safe for single-process deployments (polling mode).
# For multi-process/webhook deployments, move this to Redis.
_PENDING_TIME_REQUESTS: dict[str, dict] = {}
_TIME_PATTERN = re.compile(
    r"\b(?P<hour>[01]?\d|2[0-3])(?::(?P<minute>[0-5]\d))?\s*(?P<meridiem>am|pm)?\b",
    re.IGNORECASE,
)
_TIME_WORDS = {
    "morning": time(9, 0),
    "noon": time(12, 0),
    "afternoon": time(15, 0),
    "evening": time(19, 0),
    "night": time(21, 0),
}
_DAY_ALIASES = {
    "mon": "mon",
    "monday": "mon",
    "mondays": "mon",
    "tue": "tue",
    "tues": "tue",
    "tuesday": "tue",
    "tuesdays": "tue",
    "wed": "wed",
    "wednesday": "wed",
    "wednesdays": "wed",
    "thu": "thu",
    "thurs": "thu",
    "thursday": "thu",
    "thursdays": "thu",
    "fri": "fri",
    "friday": "fri",
    "fridays": "fri",
    "sat": "sat",
    "saturday": "sat",
    "saturdays": "sat",
    "sun": "sun",
    "sunday": "sun",
    "sundays": "sun",
}
_DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


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

        # Keyed by Telegram chat_id for per-user isolation
        pending = _PENDING_TIME_REQUESTS.get(user_id)  # use chat_id, not DB UUID
        if pending:
            response = await self._handle_pending_time(user, user_id, message, pending)
            await self._save_conversation_pair(
                user.id,
                message,
                response,
                ConversationIntent.SCHEDULING,
            )
            await self._reset_ignore(user)
            await self.db.flush()
            await self.telegram.send_message(user_id, response)
            return response

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
                for task in tasks:
                    task["scheduled_time"] = self._coerce_time_value(
                        task.get("scheduled_time"),
                        user,
                    )

                recurrence = self._detect_recurrence(message)
                if recurrence:
                    base_task = tasks[0]
                    if not base_task.get("scheduled_time"):
                        _PENDING_TIME_REQUESTS[user_id] = {
                            "tasks": [base_task],
                            "question": self._time_question(1),
                            "recurrence": recurrence,
                        }
                        response = _PENDING_TIME_REQUESTS[user_id]["question"]
                    else:
                        response = await self._schedule_recurring_tasks(
                            user.id,
                            base_task,
                            recurrence,
                        )
                else:
                    tasks_with_time = [t for t in tasks if t.get("scheduled_time")]
                    tasks_missing_time = [t for t in tasks if not t.get("scheduled_time")]

                    if tasks_with_time:
                        await self._persist_tasks(user.id, tasks_with_time)

                    if tasks_missing_time:
                        _PENDING_TIME_REQUESTS[user_id] = {
                            "tasks": tasks_missing_time,
                            "question": self._time_question(len(tasks_missing_time)),
                        }
                        if tasks_with_time:
                            response = (
                                formatter.task_confirmation(tasks_with_time)
                                + "\n\n"
                                + _PENDING_TIME_REQUESTS[user_id]["question"]
                            )
                        else:
                            response = _PENDING_TIME_REQUESTS[user_id]["question"]
                    else:
                        response = formatter.task_confirmation(tasks, agent_response=response)

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
        await self._save_conversation_pair(user.id, message, response, intent_enum)

        # 6. Reset ignore counter on any interaction
        await self._reset_ignore(user)

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
                scheduled_time = None
                raw_time = t.get("scheduled_time")
                if raw_time:
                    try:
                        scheduled_time = time.fromisoformat(raw_time)
                    except ValueError:
                        logger.warning("task_time_parse_skip", raw_time=raw_time)
                creates.append(TaskCreate(
                    description=t["description"],
                    category=TaskCategory(t.get("category", "other")),
                    difficulty=TaskDifficulty(t.get("difficulty", "medium")),
                    priority=TaskPriority(t.get("priority", "medium")),
                    scheduled_date=date.fromisoformat(t["scheduled_date"]),
                    scheduled_time=scheduled_time,
                    estimated_minutes=t.get("estimated_minutes"),
                    goal_id=None,
                    recurring_task_id=t.get("recurring_task_id"),
                ))
            except (ValueError, KeyError) as e:
                logger.warning("task_parse_skip", error=str(e), task=t)
                continue

        return await TaskCRUD.create_many(self.db, user_id, creates)

    async def _handle_pending_time(self, user, chat_id: str, message: str, pending: dict) -> str:
        parsed_time = self._extract_time_from_text(message, user)
        if not parsed_time:
            return pending.get("question") or self._time_question(len(pending.get("tasks", [])))

        tasks = pending.get("tasks", [])
        for task in tasks:
            task["scheduled_time"] = parsed_time

        recurrence = pending.get("recurrence")
        if recurrence:
            response = await self._schedule_recurring_tasks(
                user.id,
                tasks[0],
                recurrence,
            )
            _PENDING_TIME_REQUESTS.pop(chat_id, None)
            return response

        await self._persist_tasks(user.id, tasks)
        _PENDING_TIME_REQUESTS.pop(chat_id, None)
        return formatter.task_confirmation(
            tasks,
            agent_response=f"Got it. I'll remind you at {self._format_time(parsed_time)}.",
        )

    def _extract_time_from_text(self, text: str, user) -> Optional[str]:
        lowered = text.lower().strip()
        if any(term in lowered for term in ("default", "usual", "same time")):
            if user.preferred_reminder_time:
                return user.preferred_reminder_time.strftime("%H:%M")

        for word, value in _TIME_WORDS.items():
            if word in lowered:
                return value.strftime("%H:%M")

        for match in _TIME_PATTERN.finditer(lowered):
            hour = int(match.group("hour"))
            minute = int(match.group("minute") or 0)
            meridiem = match.group("meridiem")
            has_meridiem = meridiem is not None
            has_minutes = match.group("minute") is not None

            if not has_meridiem and not has_minutes:
                token = match.group(0)
                if f"at {token}" not in lowered and f"by {token}" not in lowered:
                    continue

            if has_meridiem:
                if meridiem.lower() == "pm" and hour != 12:
                    hour += 12
                if meridiem.lower() == "am" and hour == 12:
                    hour = 0

            return f"{hour:02d}:{minute:02d}"

        return None

    def _detect_recurrence(self, message: str) -> Optional[dict]:
        lowered = message.lower()
        except_days = self._extract_except_days(lowered)

        if "every day" in lowered or "everyday" in lowered or "daily" in lowered:
            frequency = RecurrenceFrequency.DAILY
            days_of_week = None
        elif "every weekday" in lowered or "weekdays" in lowered:
            frequency = RecurrenceFrequency.WEEKLY
            days_of_week = ["mon", "tue", "wed", "thu", "fri"]
        elif "every weekend" in lowered or "weekends" in lowered:
            frequency = RecurrenceFrequency.WEEKLY
            days_of_week = ["sat", "sun"]
        else:
            days = self._extract_days_from_text(lowered)
            if days:
                frequency = RecurrenceFrequency.WEEKLY
                days_of_week = days
            else:
                return None

        if days_of_week and except_days:
            days_of_week = [d for d in days_of_week if d not in except_days]

        if frequency == RecurrenceFrequency.WEEKLY and days_of_week is not None and not days_of_week:
            return None

        return {
            "frequency": frequency,
            "days_of_week": days_of_week,
            "except_days": except_days,
        }

    def _extract_days_from_text(self, text: str) -> list[str]:
        found = {day for key, day in _DAY_ALIASES.items() if re.search(rf"\b{key}\b", text)}
        return [day for day in _DAY_ORDER if day in found]

    def _extract_except_days(self, text: str) -> list[str]:
        if "except" not in text:
            return []
        except_segment = text.split("except", 1)[1]
        return self._extract_days_from_text(except_segment)

    async def _schedule_recurring_tasks(
        self,
        user_id: str,
        base_task: dict,
        recurrence: dict,
    ) -> str:
        raw_start = date.fromisoformat(base_task.get("scheduled_date", date.today().isoformat()))
        start_date = max(raw_start, date.today())
        scheduled_time = base_task.get("scheduled_time")
        recurring = await RecurringTaskCRUD.create(
            self.db,
            user_id,
            {
                "description": base_task["description"],
                "category": base_task.get("category", "other"),
                "difficulty": base_task.get("difficulty", "medium"),
                "priority": base_task.get("priority", "medium"),
                "scheduled_time": time.fromisoformat(scheduled_time) if scheduled_time else None,
                "start_date": start_date,
                "end_date": None,
                "frequency": recurrence["frequency"],
                "days_of_week": ",".join(recurrence["days_of_week"]) if recurrence.get("days_of_week") else None,
                "except_days": ",".join(recurrence["except_days"]) if recurrence.get("except_days") else None,
            },
        )

        created_tasks = await self._materialize_recurring_instances(
            user_id,
            recurring,
            start_date,
        )

        response_note = self._format_recurrence_note(recurrence, scheduled_time)
        display_tasks = created_tasks[:7]
        if not display_tasks:
            return f"✅ Recurring task saved. {response_note}"
        return formatter.task_confirmation(display_tasks, agent_response=response_note)

    async def _materialize_recurring_instances(
        self,
        user_id: str,
        recurring,
        start_date: date,
    ) -> list[dict]:
        lookahead_days = settings.recurrence_lookahead_days
        end_date = start_date + timedelta(days=lookahead_days - 1)
        if recurring.end_date and recurring.end_date < end_date:
            end_date = recurring.end_date

        days_of_week = recurring.days_of_week.split(",") if recurring.days_of_week else None
        except_days = recurring.except_days.split(",") if recurring.except_days else []
        dates = self._generate_recurrence_dates(
            start_date,
            end_date,
            recurring.frequency,
            days_of_week,
            except_days,
        )

        existing = await TaskCRUD.get_recurring_dates_in_range(
            self.db,
            recurring.id,
            start_date,
            end_date,
        )

        task_dicts = []
        for task_date in dates:
            if task_date in existing:
                continue
            task_dicts.append(
                {
                    "description": recurring.description,
                    "category": recurring.category,
                    "difficulty": recurring.difficulty,
                    "priority": recurring.priority,
                    "scheduled_date": task_date.isoformat(),
                    "scheduled_time": recurring.scheduled_time.strftime("%H:%M") if recurring.scheduled_time else None,
                    "estimated_minutes": None,
                    "recurring_task_id": recurring.id,
                }
            )

        if task_dicts:
            await self._persist_tasks(user_id, task_dicts)

        if dates:
            await RecurringTaskCRUD.update_last_generated(self.db, recurring.id, end_date)

        return task_dicts

    def _generate_recurrence_dates(
        self,
        start_date: date,
        end_date: date,
        frequency: RecurrenceFrequency,
        days_of_week: Optional[list[str]],
        except_days: list[str],
    ) -> list[date]:
        dates: list[date] = []
        current = start_date
        day_index = {day: i for i, day in enumerate(_DAY_ORDER)}

        allowed_days = None
        if days_of_week:
            allowed_days = {day_index[d] for d in days_of_week if d in day_index}
        if frequency == RecurrenceFrequency.WEEKLY and allowed_days is not None and not allowed_days:
            return []
        excluded_days = {day_index[d] for d in except_days if d in day_index}

        while current <= end_date:
            weekday = current.weekday()
            if weekday in excluded_days:
                current += timedelta(days=1)
                continue

            if frequency == RecurrenceFrequency.DAILY:
                dates.append(current)
            elif frequency == RecurrenceFrequency.WEEKLY:
                if allowed_days is None or weekday in allowed_days:
                    dates.append(current)

            current += timedelta(days=1)

        return dates

    def _format_recurrence_note(self, recurrence: dict, scheduled_time: Optional[str]) -> str:
        frequency = recurrence["frequency"].value
        except_days = recurrence.get("except_days") or []
        days_of_week = recurrence.get("days_of_week") or []

        if frequency == "daily":
            base = "Repeats daily"
        else:
            base = "Repeats weekly on " + ", ".join(d.capitalize() for d in days_of_week)

        if except_days:
            base += " except " + ", ".join(d.capitalize() for d in except_days)

        if scheduled_time:
            base += f" at {self._format_time(scheduled_time)}"

        return base + "."

    def _coerce_time_value(self, value: Optional[str], user) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, str):
            try:
                return time.fromisoformat(value).strftime("%H:%M")
            except ValueError:
                return self._extract_time_from_text(value, user)
        return None

    def _format_time(self, time_str: str) -> str:
        try:
            return time.fromisoformat(time_str).strftime("%I:%M %p").lstrip("0")
        except ValueError:
            return time_str

    def _time_question(self, task_count: int) -> str:
        count_text = "this task" if task_count == 1 else "these tasks"
        return (
            f"What time should I remind you for {count_text}? "
            "You can say something like '6pm', '18:30', or 'evening'."
        )

    async def _save_conversation_pair(
        self,
        user_id: str,
        message: str,
        response: str,
        intent_enum: Optional[ConversationIntent],
    ) -> None:
        summary = response[:100] if response else None
        await ConversationCRUD.save_conversation(
            self.db,
            user_id=user_id,
            role="user",
            content=message,
            intent=intent_enum,
            summary=message[:100],
        )
        await ConversationCRUD.save_conversation(
            self.db,
            user_id=user_id,
            role="assistant",
            content=response,
            intent=intent_enum,
            summary=summary,
        )

    async def _reset_ignore(self, user) -> None:
        if user.consecutive_ignores > 0:
            user.consecutive_ignores = 0
            user.dormant_mode = False

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
