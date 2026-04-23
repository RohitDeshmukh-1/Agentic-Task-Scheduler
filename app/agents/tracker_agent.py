"""
Tracker Agent — processes task completion responses and updates statuses.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import SYSTEM_PERSONA, TRACKER_PROMPT
from app.agents.state import GraphState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _format_tasks_list(tasks: list[dict]) -> str:
    """Format pending tasks for the LLM prompt."""
    if not tasks:
        return "No tasks scheduled for today."
    lines = []
    for i, t in enumerate(tasks, 1):
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "missed": "❌"}.get(
            t.get("status", "pending"), "⏳"
        )
        lines.append(f"{i}. {status_icon} {t['description']} [{t.get('difficulty', 'medium')}]")
    return "\n".join(lines)


async def tracker_agent(state: GraphState, llm) -> GraphState:
    """Parse user's completion response and determine task status changes."""
    user_ctx = state.get("user_context", {})
    message = state.get("user_message", "")
    pending_tasks = user_ctx.get("pending_tasks_today", [])

    tasks_list = _format_tasks_list(pending_tasks)

    prompt = TRACKER_PROMPT.format(
        message=message,
        tasks_list=tasks_list,
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

        modifications = result.get("modifications", [])
        resp = result.get("response", "Got it! I've updated your tasks.")
        all_completed = result.get("all_completed", False)

        # Map modifications to actual task IDs
        mapped_mods = []
        for mod in modifications:
            desc = mod.get("task_description", "")
            # Find matching task by fuzzy description match
            matched_task = None
            for t in pending_tasks:
                if desc.lower() in t.get("description", "").lower() or \
                   t.get("description", "").lower() in desc.lower():
                    matched_task = t
                    break

            if matched_task:
                mapped_mods.append({
                    "task_id": matched_task.get("id", ""),
                    "task_description": matched_task.get("description", desc),
                    "new_status": mod.get("new_status", "completed"),
                    "reschedule_date": mod.get("reschedule_date"),
                    "notes": mod.get("notes"),
                })

        # If "all_completed" and no specific mods, mark everything
        if all_completed and not mapped_mods:
            for t in pending_tasks:
                mapped_mods.append({
                    "task_id": t.get("id", ""),
                    "task_description": t.get("description", ""),
                    "new_status": "completed",
                    "reschedule_date": None,
                    "notes": None,
                })

        state["task_modifications"] = mapped_mods
        state["response"] = resp

        logger.info(
            "tasks_tracked",
            modifications=len(mapped_mods),
            all_completed=all_completed,
        )

    except (json.JSONDecodeError, Exception) as e:
        logger.error("tracker_error", error=str(e))
        state["task_modifications"] = []
        state["response"] = (
            "I couldn't quite parse that. Could you tell me which tasks you completed? "
            "You can say 'all done', 'none', or 'I did task 1 and 3'."
        )
        state["error"] = str(e)

    return state
