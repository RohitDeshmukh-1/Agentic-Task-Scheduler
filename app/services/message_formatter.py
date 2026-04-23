"""
Message formatter — creates beautiful WhatsApp-formatted messages.
"""

from __future__ import annotations

from datetime import date
from typing import Optional


class MessageFormatter:
    """Format messages for WhatsApp with proper styling."""

    @staticmethod
    def morning_reminder(tasks: list[dict], streak: int, level: int, xp: int) -> str:
        if not tasks:
            return "☀️ *Good morning!*\n\nYou have a free day — no tasks scheduled. Enjoy it or add something new!"

        lines = [
            f"☀️ *Good Morning!* Rise and conquer!",
            f"🔥 Streak: *{streak} days* | ⭐ Level {level} | 💎 {xp} XP",
            "",
            f"📋 *Today's Mission ({len(tasks)} tasks):*",
            "",
        ]

        for i, task in enumerate(tasks, 1):
            priority_icon = {
                "urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"
            }.get(task.get("priority", "medium"), "🟡")
            diff_label = task.get("difficulty", "medium").capitalize()
            time_str = f" at {task.get('scheduled_time', '')}" if task.get("scheduled_time") else ""
            lines.append(f"{priority_icon} {i}. {task['description']}{time_str} _({diff_label})_")

        lines.extend([
            "",
            "💪 You've got this! Reply when you're done or need to reschedule.",
        ])
        return "\n".join(lines)

    @staticmethod
    def night_check(tasks: list[dict], user_name: Optional[str] = None) -> str:
        name = user_name or "there"
        if not tasks:
            return f"🌙 Hey {name}! No tasks were scheduled today. Rest well!"

        pending = [t for t in tasks if t.get("status") in ("pending", "in_progress")]
        completed = [t for t in tasks if t.get("status") == "completed"]

        lines = [
            f"🌙 *Evening Check-in!*",
            "",
            f"📊 Today's progress: *{len(completed)}/{len(tasks)}* tasks",
            "",
        ]

        if pending:
            lines.append("⏳ *Still pending:*")
            for i, t in enumerate(pending, 1):
                lines.append(f"  {i}. {t['description']}")
            lines.extend([
                "",
                "Did you complete these? Reply:",
                "• *'Yes'* — all done ✅",
                "• *'Done 1, 3'* — specific tasks",
                "• *'Reschedule 2'* — move to tomorrow",
                "• *'No'* — mark as missed",
            ])
        else:
            lines.extend([
                "🎉 *All tasks completed!* Amazing work!",
                f"Keep the streak alive tomorrow! 🔥",
            ])

        return "\n".join(lines)

    @staticmethod
    def task_confirmation(tasks: list[dict]) -> str:
        if not tasks:
            return "Hmm, I couldn't extract any tasks. Could you try again?"

        lines = ["✅ *Tasks scheduled!*", ""]
        for i, t in enumerate(tasks, 1):
            date_str = t.get("scheduled_date", "today")
            lines.append(f"{i}. {t['description']} — 📅 {date_str}")
        lines.extend(["", "I'll remind you when it's time! 🔔"])
        return "\n".join(lines)

    @staticmethod
    def streak_update(streak: int, xp_earned: int, level: int, leveled_up: bool) -> str:
        lines = []
        if leveled_up:
            lines.append(f"🎊 *LEVEL UP!* You're now Level {level}! 🎊")
        lines.append(f"🔥 Streak: *{streak} days* | +{xp_earned} XP earned")
        if streak >= 7:
            lines.append("🏆 One week strong! Incredible consistency!")
        elif streak >= 3:
            lines.append("⚡ Building momentum! Keep it up!")
        return "\n".join(lines)

    @staticmethod
    def weekly_report(report: dict, user_context: dict) -> str:
        lines = [
            "📊 *Weekly Report*",
            f"📅 {report.get('week_start', '')} → {report.get('week_end', '')}",
            "",
            report.get("summary", ""),
            "",
            f"✅ Completed: *{report.get('completed_tasks', 0)}*/{report.get('total_tasks', 0)}",
            f"📈 Rate: *{report.get('completion_rate', 0):.0%}*",
            f"💎 XP earned: *{report.get('xp_earned', 0)}*",
            f"🔥 Streak: *{user_context.get('current_streak', 0)} days*",
            "",
            "💡 *Insights:*",
        ]
        for insight in report.get("insights", []):
            lines.append(f"  • {insight}")

        best = report.get("best_day")
        worst = report.get("worst_day")
        if best:
            lines.append(f"\n🏆 Best day: *{best}*")
        if worst:
            lines.append(f"📉 Needs work: *{worst}*")

        lines.extend(["", report.get("sign_off", "Keep going! 💪")])
        return "\n".join(lines)

    @staticmethod
    def dormant_reengagement(name: Optional[str] = None) -> str:
        n = name or "there"
        return (
            f"👋 Hey {n}! I noticed you've been quiet for a while.\n\n"
            "No pressure — whenever you're ready, just send me a task "
            "and we'll pick right back up! 🚀\n\n"
            "Even one small task counts. What's on your plate today?"
        )

    @staticmethod
    def goal_confirmation(goal: dict) -> str:
        lines = [
            "🎯 *Goal Set!*",
            "",
            f"*{goal.get('title', 'Your goal')}*",
        ]
        if goal.get("description"):
            lines.append(f"_{goal['description']}_")
        if goal.get("target_date"):
            lines.append(f"📅 Target: {goal['target_date']}")
        lines.extend(["", "I'll help you break this down into daily tasks. Let's do this! 💪"])
        return "\n".join(lines)
