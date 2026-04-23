"""
Planner Agent — extracts tasks from natural language and structures them.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import PLANNER_PROMPT, SYSTEM_PERSONA
from app.agents.state import GraphState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def planner_agent(state: GraphState, llm) -> GraphState:
    """Extract tasks from user message and produce structured output."""
    user_ctx = state.get("user_context", {})
    message = state.get("user_message", "")
    today = date.today()

    # Format active goals for context
    goals = user_ctx.get("active_goals", [])
    goals_str = ", ".join(g.get("title", "") for g in goals) if goals else "None set"

    prompt = PLANNER_PROMPT.format(
        message=message,
        today=today.isoformat(),
        tomorrow=(today + timedelta(days=1)).isoformat(),
        completion_rate=user_ctx.get("recent_completion_rate", 0.0),
        streak=user_ctx.get("current_streak", 0),
        goals=goals_str,
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

        tasks = result.get("tasks", [])
        resp = result.get("response", "")

        # Validate and sanitize dates
        for task in tasks:
            try:
                date.fromisoformat(task.get("scheduled_date", ""))
            except (ValueError, TypeError):
                task["scheduled_date"] = today.isoformat()

            # Ensure required fields
            task.setdefault("category", "other")
            task.setdefault("difficulty", "medium")
            task.setdefault("priority", "medium")

        state["extracted_tasks"] = tasks
        state["response"] = resp

        logger.info("tasks_extracted", count=len(tasks))

    except (json.JSONDecodeError, Exception) as e:
        logger.error("planner_error", error=str(e))
        state["extracted_tasks"] = []
        state["response"] = (
            "I had a little trouble understanding that. "
            "Could you rephrase? For example: 'Remind me to study math tomorrow at 3pm'"
        )
        state["error"] = str(e)

    return state
