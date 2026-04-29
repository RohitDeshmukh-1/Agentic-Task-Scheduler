"""
Telegram formatting utilities — inline keyboards, message formatting, etc.
"""

from __future__ import annotations

from typing import Optional


class TelegramFormatter:
    """Helper class for Telegram message formatting."""

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold."""
        return f"<b>{text}</b>"

    @staticmethod
    def italic(text: str) -> str:
        """Format text as italic."""
        return f"<i>{text}</i>"

    @staticmethod
    def code(text: str) -> str:
        """Format text as code."""
        return f"<code>{text}</code>"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Format text as link."""
        return f'<a href="{url}">{text}</a>'

    @staticmethod
    def inline_keyboard(buttons: list[list[dict]]) -> dict:
        """
        Create inline keyboard markup.
        
        Args:
            buttons: List of button rows, each row is a list of button dicts
                     Each button should have 'text' and 'callback_data' or 'url'
        
        Example:
            buttons = [
                [{"text": "Yes", "callback_data": "yes"},
                 {"text": "No", "callback_data": "no"}],
                [{"text": "View", "url": "https://example.com"}]
            ]
        """
        return {"inline_keyboard": buttons}

    @staticmethod
    def reply_keyboard(
        buttons: list[list[str]],
        one_time: bool = True,
        selective: bool = False,
    ) -> dict:
        """
        Create reply keyboard markup.
        
        Args:
            buttons: List of button rows
            one_time: Hide keyboard after selection
            selective: Show only to mentioned users
        """
        keyboard = {"keyboard": [[{"text": b} for b in row] for row in buttons]}
        keyboard["one_time_keyboard"] = one_time
        keyboard["selective"] = selective
        return keyboard

    @staticmethod
    def remove_keyboard() -> dict:
        """Remove custom keyboard."""
        return {"remove_keyboard": True}

    @staticmethod
    def format_task_list(tasks: list[dict]) -> str:
        """Format a list of tasks for Telegram."""
        if not tasks:
            return "📋 <b>No tasks yet!</b>\n\nTap /add to create your first task."

        text = "📋 <b>Your Tasks</b>\n\n"
        for i, task in enumerate(tasks, 1):
            status_emoji = "✅" if task.get("status") == "completed" else "⭕"
            priority = task.get("priority", "medium").upper()
            text += f"{status_emoji} <b>{task.get('title')}</b>\n"
            text += f"   Priority: {priority}\n"
            if task.get("due_date"):
                text += f"   Due: {task['due_date']}\n"
            text += "\n"

        return text

    @staticmethod
    def format_goal_item(goal: dict) -> str:
        """Format a single goal for display."""
        text = f"🎯 <b>{goal.get('title')}</b>\n"
        text += f"   {goal.get('description', 'No description')}\n"
        if goal.get("target_date"):
            text += f"   Target: {goal['target_date']}\n"
        return text

    @staticmethod
    def format_daily_summary(summary: dict) -> str:
        """Format daily summary for Telegram."""
        text = "📊 <b>Daily Summary</b>\n\n"
        text += f"✅ Completed: {summary.get('completed', 0)}\n"
        text += f"⏳ Pending: {summary.get('pending', 0)}\n"
        text += f"📈 Progress: {summary.get('progress_percent', 0)}%\n"
        text += f"🎯 Productivity Score: {summary.get('productivity_score', 'N/A')}\n"
        return text

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters."""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        return text


class TelegramKeyboards:
    """Pre-built keyboard layouts for common interactions."""

    @staticmethod
    def main_menu() -> dict:
        """Main menu keyboard."""
        return TelegramFormatter.inline_keyboard(
            [
                [
                    {"text": "📝 New Task", "callback_data": "add_task"},
                    {"text": "📋 My Tasks", "callback_data": "list_tasks"},
                ],
                [
                    {"text": "🎯 Goals", "callback_data": "list_goals"},
                    {"text": "📊 Summary", "callback_data": "daily_summary"},
                ],
                [
                    {"text": "⚙️ Settings", "callback_data": "settings"},
                    {"text": "❓ Help", "callback_data": "help"},
                ],
            ]
        )

    @staticmethod
    def task_actions() -> dict:
        """Actions for a single task."""
        return TelegramFormatter.inline_keyboard(
            [
                [
                    {"text": "✅ Complete", "callback_data": "complete_task"},
                    {"text": "✏️ Edit", "callback_data": "edit_task"},
                ],
                [
                    {"text": "🗑️ Delete", "callback_data": "delete_task"},
                    {"text": "🔙 Back", "callback_data": "list_tasks"},
                ],
            ]
        )

    @staticmethod
    def confirm_action(action: str = "delete") -> dict:
        """Confirmation keyboard."""
        return TelegramFormatter.inline_keyboard(
            [
                [
                    {"text": "✅ Yes", "callback_data": f"confirm_{action}"},
                    {"text": "❌ No", "callback_data": "cancel"},
                ],
            ]
        )

    @staticmethod
    def priority_buttons() -> dict:
        """Priority selection buttons."""
        return TelegramFormatter.inline_keyboard(
            [
                [
                    {"text": "🔴 High", "callback_data": "priority_high"},
                    {"text": "🟡 Medium", "callback_data": "priority_medium"},
                    {"text": "🟢 Low", "callback_data": "priority_low"},
                ],
            ]
        )

    @staticmethod
    def time_quick_select() -> dict:
        """Quick time selection for reminders."""
        return TelegramFormatter.inline_keyboard(
            [
                [
                    {"text": "Today", "callback_data": "due_today"},
                    {"text": "Tomorrow", "callback_data": "due_tomorrow"},
                    {"text": "This Week", "callback_data": "due_week"},
                ],
                [
                    {"text": "Custom", "callback_data": "due_custom"},
                    {"text": "No Deadline", "callback_data": "due_none"},
                ],
            ]
        )
