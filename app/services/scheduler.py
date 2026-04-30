"""
APScheduler-based background jobs for reminders and reports.
"""

from __future__ import annotations

from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.crud.daily_log import DailyLogCRUD
from app.crud.recurring_task import RecurringTaskCRUD
from app.crud.task import TaskCRUD
from app.crud.user import UserCRUD
from app.models.recurring_task import RecurrenceFrequency
from app.models.task import TaskCategory, TaskDifficulty, TaskPriority
from app.schemas.task import TaskCreate
from app.services.message_formatter import MessageFormatter
from app.services.telegram import get_telegram_service

logger = get_logger(__name__)
settings = get_settings()
formatter = MessageFormatter()

scheduler = AsyncIOScheduler()

_DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


async def morning_reminder_job():
    """Send morning task list to all active users."""
    logger.info("job_started", job="morning_reminder")
    telegram = get_telegram_service()
    
    async with async_session_factory() as db:
        users = await UserCRUD.list_active(db)
        today = date.today()

        for user in users:
            if user.dormant_mode:
                # Send re-engagement instead
                msg = formatter.dormant_reengagement(user.display_name)
                await telegram.send_message(user.phone_number, msg)
                continue

            tasks = await TaskCRUD.get_tasks_for_date(db, user.id, today)
            if not tasks:
                continue

            task_dicts = [
                {
                    "description": t.description,
                    "priority": t.priority.value,
                    "difficulty": t.difficulty.value,
                    "scheduled_time": str(t.scheduled_time) if t.scheduled_time else None,
                }
                for t in tasks
            ]

            msg = formatter.morning_reminder(
                task_dicts, user.current_streak, user.level, user.total_xp
            )
            await telegram.send_message(user.phone_number, msg)

        await db.commit()
    logger.info("job_completed", job="morning_reminder")


async def night_check_job():
    """Send evening completion check to all active users."""
    logger.info("job_started", job="night_check")
    telegram = get_telegram_service()

    async with async_session_factory() as db:
        users = await UserCRUD.list_active(db)
        today = date.today()

        for user in users:
            if user.dormant_mode:
                continue

            tasks = await TaskCRUD.get_tasks_for_date(db, user.id, today)
            if not tasks:
                continue

            task_dicts = [
                {"description": t.description, "status": t.status.value}
                for t in tasks
            ]

            msg = formatter.night_check(task_dicts, user.display_name)
            await telegram.send_message(user.phone_number, msg)

            # Track if user ignores (will be reset when they respond)
            await UserCRUD.increment_ignore(db, user)

        await db.commit()
    logger.info("job_completed", job="night_check")


async def weekly_report_job():
    """Generate and send weekly reports every Sunday."""
    logger.info("job_started", job="weekly_report")
    telegram = get_telegram_service()

    async with async_session_factory() as db:
        users = await UserCRUD.list_active(db)
        today = date.today()

        for user in users:
            weekly = await DailyLogCRUD.get_weekly_stats(db, user.id, today)

            if weekly["total_tasks"] == 0:
                continue

            # Use analyzer agent for insights
            try:
                from app.agents.analyzer_agent import analyzer_agent
                from app.agents.graph import _get_llm
                llm = _get_llm()
                user_ctx = {
                    "user_id": user.id,
                    "current_streak": user.current_streak,
                    "longest_streak": user.longest_streak,
                    "level": user.level,
                }
                report = await analyzer_agent(weekly, user_ctx, llm)
                report["week_start"] = str(weekly["week_start"])
                report["week_end"] = str(weekly["week_end"])
                report["total_tasks"] = weekly["total_tasks"]
                report["completed_tasks"] = weekly["completed_tasks"]
                report["completion_rate"] = weekly["completion_rate"]
                report["xp_earned"] = weekly["xp_earned"]
            except Exception as e:
                logger.error("report_generation_error", error=str(e))
                report = {
                    "summary": f"This week: {weekly['completed_tasks']}/{weekly['total_tasks']} tasks done.",
                    "insights": [],
                    "best_day": "N/A",
                    "worst_day": "N/A",
                    "sign_off": "Keep going!",
                    **weekly,
                }

            msg = formatter.weekly_report(report, {
                "current_streak": user.current_streak,
            })
            await telegram.send_message(user.phone_number, msg)

        await db.commit()
    logger.info("job_completed", job="weekly_report")


async def auto_reschedule_job():
    """Auto-reschedule missed tasks from yesterday."""
    logger.info("job_started", job="auto_reschedule")

    async with async_session_factory() as db:
        users = await UserCRUD.list_active(db)
        yesterday = date.today() - timedelta(days=1)

        for user in users:
            rescheduled = await TaskCRUD.auto_reschedule_missed(
                db, user.id, yesterday
            )
            if rescheduled:
                logger.info(
                    "tasks_auto_rescheduled",
                    user=user.phone_number,
                    count=len(rescheduled),
                )

        await db.commit()
    logger.info("job_completed", job="auto_reschedule")


def _generate_recurrence_dates(
    start_date: date,
    end_date: date,
    frequency: RecurrenceFrequency,
    days_of_week: list[str] | None,
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


async def recurring_task_job():
    """Materialize upcoming tasks for recurring rules."""
    logger.info("job_started", job="recurring_tasks")

    async with async_session_factory() as db:
        recurrences = await RecurringTaskCRUD.list_active(db)
        today = date.today()
        lookahead = settings.recurrence_lookahead_days

        for rule in recurrences:
            start = max(rule.start_date, today)
            if rule.last_generated_date and rule.last_generated_date >= start:
                start = rule.last_generated_date + timedelta(days=1)

            end = today + timedelta(days=lookahead - 1)
            if rule.end_date and rule.end_date < end:
                end = rule.end_date

            if start > end:
                continue

            days_of_week = rule.days_of_week.split(",") if rule.days_of_week else None
            except_days = rule.except_days.split(",") if rule.except_days else []
            dates = _generate_recurrence_dates(
                start,
                end,
                rule.frequency,
                days_of_week,
                except_days,
            )

            if not dates:
                await RecurringTaskCRUD.update_last_generated(db, rule.id, end)
                continue

            existing = await TaskCRUD.get_recurring_dates_in_range(db, rule.id, start, end)

            creates = []
            for task_date in dates:
                if task_date in existing:
                    continue
                creates.append(
                    TaskCreate(
                        description=rule.description,
                        category=TaskCategory(rule.category),
                        difficulty=TaskDifficulty(rule.difficulty),
                        priority=TaskPriority(rule.priority),
                        scheduled_date=task_date,
                        scheduled_time=rule.scheduled_time,
                        estimated_minutes=None,
                        goal_id=None,
                        recurring_task_id=rule.id,
                    )
                )

            if creates:
                await TaskCRUD.create_many(db, rule.user_id, creates)

            await RecurringTaskCRUD.update_last_generated(db, rule.id, end)

        await db.commit()
    logger.info("job_completed", job="recurring_tasks")


# ─── Day mapping ─────────────────────────────────────────────────────────────
DAY_MAP = {"mon": "mon", "tue": "tue", "wed": "wed", "thu": "thu", "fri": "fri", "sat": "sat", "sun": "sun"}


def setup_scheduler():
    """Configure and start all scheduled jobs."""
    # Morning reminder
    scheduler.add_job(
        morning_reminder_job,
        "cron",
        hour=settings.morning_reminder_hour,
        minute=settings.morning_reminder_minute,
        id="morning_reminder",
        replace_existing=True,
    )

    # Night check
    scheduler.add_job(
        night_check_job,
        "cron",
        hour=settings.night_check_hour,
        minute=settings.night_check_minute,
        id="night_check",
        replace_existing=True,
    )

    # Weekly report
    scheduler.add_job(
        weekly_report_job,
        "cron",
        day_of_week=settings.weekly_report_day,
        hour=settings.weekly_report_hour,
        id="weekly_report",
        replace_existing=True,
    )

    # Auto-reschedule (runs daily at 7 AM, before morning reminder)
    scheduler.add_job(
        auto_reschedule_job,
        "cron",
        hour=7,
        minute=30,
        id="auto_reschedule",
        replace_existing=True,
    )

    # Recurring task materialization (runs daily)
    scheduler.add_job(
        recurring_task_job,
        "cron",
        hour=1,
        minute=15,
        id="recurring_tasks",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
