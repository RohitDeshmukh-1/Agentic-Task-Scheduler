"""
Router Agent — classifies user intent to dispatch to the correct agent.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts import ROUTER_PROMPT
from app.agents.state import GraphState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def router_agent(state: GraphState, llm) -> GraphState:
    """Classify the user's message intent and update state."""
    user_ctx = state.get("user_context", {})
    message = state.get("user_message", "")

    prompt = ROUTER_PROMPT.format(
        message=message,
        streak=user_ctx.get("current_streak", 0),
        pending_count=len(user_ctx.get("pending_tasks_today", [])),
        dormant=user_ctx.get("dormant_mode", False),
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are an intent classifier. Respond only with valid JSON."),
            HumanMessage(content=prompt),
        ])

        # Parse the JSON response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        intent = result.get("intent", "general_chat")
        confidence = result.get("confidence", 0.5)

        logger.info(
            "intent_classified",
            intent=intent,
            confidence=confidence,
            message_preview=message[:50],
        )

        # Fallback for low confidence
        if confidence < 0.3:
            intent = "general_chat"

        state["current_intent"] = intent

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("router_fallback", error=str(e))
        state["current_intent"] = "general_chat"

    return state
