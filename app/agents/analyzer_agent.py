"""
Analyzer Agent — generates weekly reports with AI-powered insights.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import ANALYZER_PROMPT, SYSTEM_PERSONA
from app.core.logging import get_logger

logger = get_logger(__name__)


async def analyzer_agent(weekly_data: dict, user_context: dict, llm) -> dict:
    """Generate a weekly report with AI insights."""
    daily_logs = weekly_data.get("daily_logs", [])
    daily_breakdown = "\n".join(
        f"- {l.date.strftime('%A')}: {l.completed_tasks}/{l.total_tasks} ({l.completion_rate:.0%})"
        for l in daily_logs
    ) or "No data"

    prompt = ANALYZER_PROMPT.format(
        week_start=weekly_data.get("week_start", "N/A"),
        week_end=weekly_data.get("week_end", "N/A"),
        total_tasks=weekly_data.get("total_tasks", 0),
        completed=weekly_data.get("completed_tasks", 0),
        completion_rate=weekly_data.get("completion_rate", 0.0),
        missed=weekly_data.get("missed_tasks", 0),
        rescheduled=weekly_data.get("rescheduled_tasks", 0),
        xp=weekly_data.get("xp_earned", 0),
        streak=user_context.get("current_streak", 0),
        longest_streak=user_context.get("longest_streak", 0),
        level=user_context.get("level", 1),
        daily_breakdown=daily_breakdown,
        category_breakdown="See dashboard for details.",
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PERSONA),
            HumanMessage(content=prompt),
        ])
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        result = json.loads(content)
        logger.info("weekly_report_generated")
        return result
    except Exception as e:
        logger.error("analyzer_error", error=str(e))
        return {
            "summary": f"Completed {weekly_data.get('completed_tasks', 0)}/{weekly_data.get('total_tasks', 0)} tasks.",
            "insights": ["Keep tracking for better insights!"],
            "best_day": "N/A",
            "worst_day": "N/A",
            "sign_off": "Keep going! 💪",
        }
