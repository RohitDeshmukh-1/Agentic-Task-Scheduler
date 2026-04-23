"""
LangGraph Orchestrator — the main graph that routes messages through agents.
"""

from __future__ import annotations

from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agents.planner_agent import planner_agent
from app.agents.prompts import GENERAL_CHAT_PROMPT, HELP_RESPONSE, QUERY_PROMPT, SYSTEM_PERSONA
from app.agents.router_agent import router_agent
from app.agents.state import GraphState
from app.agents.tracker_agent import tracker_agent
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _get_llm():
    """Create the LLM instance based on configuration."""
    return ChatGroq(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.3,
        max_tokens=2048,
    )


# ─── Node Functions ──────────────────────────────────────────────────────────

async def route_node(state: GraphState) -> GraphState:
    llm = _get_llm()
    return await router_agent(state, llm)


async def plan_node(state: GraphState) -> GraphState:
    llm = _get_llm()
    return await planner_agent(state, llm)


async def track_node(state: GraphState) -> GraphState:
    llm = _get_llm()
    return await tracker_agent(state, llm)


async def query_node(state: GraphState) -> GraphState:
    """Handle user queries about tasks/progress."""
    llm = _get_llm()
    ctx = state.get("user_context", {})
    today_tasks = ctx.get("pending_tasks_today", [])
    tasks_str = "\n".join(
        f"{i}. {'✅' if t.get('status') == 'completed' else '⏳'} {t['description']}"
        for i, t in enumerate(today_tasks, 1)
    ) or "No tasks today"

    goals = ctx.get("active_goals", [])
    goals_str = ", ".join(g.get("title", "") for g in goals) or "None"

    prompt = QUERY_PROMPT.format(
        today=date.today().isoformat(),
        streak=ctx.get("current_streak", 0),
        longest_streak=ctx.get("longest_streak", 0),
        level=ctx.get("level", 1),
        xp=ctx.get("total_xp", 0),
        today_tasks=tasks_str,
        goals=goals_str,
        week_rate=ctx.get("recent_completion_rate", 0.0),
        message=state.get("user_message", ""),
    )

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PERSONA),
        HumanMessage(content=prompt),
    ])
    state["response"] = response.content.strip()
    return state


async def help_node(state: GraphState) -> GraphState:
    state["response"] = HELP_RESPONSE
    return state


async def chat_node(state: GraphState) -> GraphState:
    """Handle general chat / greetings."""
    llm = _get_llm()
    ctx = state.get("user_context", {})
    prompt = GENERAL_CHAT_PROMPT.format(
        message=state.get("user_message", ""),
        name=ctx.get("display_name") or "there",
        streak=ctx.get("current_streak", 0),
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    state["response"] = response.content.strip()
    return state


async def goal_node(state: GraphState) -> GraphState:
    """Handle goal setting — extract goal info and confirm."""
    llm = _get_llm()
    prompt = f"""Extract the goal from this message and respond with JSON:
{{"title": "goal title", "description": "brief description", "target_date": "YYYY-MM-DD or null", "category": "category", "response": "confirmation message"}}

Message: "{state.get('user_message', '')}"
Today: {date.today().isoformat()}"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PERSONA),
        HumanMessage(content=prompt),
    ])

    import json
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        result = json.loads(content)
        state["goal_data"] = result
        state["response"] = result.get("response", "Goal noted! 🎯")
    except Exception:
        state["response"] = "I'd love to help you set a goal! Could you tell me what you'd like to achieve and by when?"

    return state


# ─── Routing Logic ───────────────────────────────────────────────────────────

def intent_router(state: GraphState) -> str:
    """Conditional edge: route to the correct agent based on classified intent."""
    intent = state.get("current_intent", "general_chat")
    route_map = {
        "scheduling": "planner",
        "status_update": "tracker",
        "goal_setting": "goal_setter",
        "query": "query_handler",
        "help": "help_handler",
        "general_chat": "chat_handler",
    }
    return route_map.get(intent, "chat_handler")


# ─── Graph Construction ─────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent pipeline."""
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("router", route_node)
    graph.add_node("planner", plan_node)
    graph.add_node("tracker", track_node)
    graph.add_node("query_handler", query_node)
    graph.add_node("help_handler", help_node)
    graph.add_node("chat_handler", chat_node)
    graph.add_node("goal_setter", goal_node)

    # Entry point
    graph.set_entry_point("router")

    # Conditional routing from router
    graph.add_conditional_edges(
        "router",
        intent_router,
        {
            "planner": "planner",
            "tracker": "tracker",
            "query_handler": "query_handler",
            "help_handler": "help_handler",
            "chat_handler": "chat_handler",
            "goal_setter": "goal_setter",
        },
    )

    # All agents terminate after producing a response
    graph.add_edge("planner", END)
    graph.add_edge("tracker", END)
    graph.add_edge("query_handler", END)
    graph.add_edge("help_handler", END)
    graph.add_edge("chat_handler", END)
    graph.add_edge("goal_setter", END)

    return graph.compile()


# ─── Public API ──────────────────────────────────────────────────────────────

_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def process_message(user_message: str, user_context: dict) -> GraphState:
    """Main entry point: process a user message through the agent pipeline."""
    graph = _get_graph()

    initial_state: GraphState = {
        "messages": [],
        "user_message": user_message,
        "current_intent": "",
        "user_context": user_context,
        "extracted_tasks": [],
        "task_modifications": [],
        "goal_data": None,
        "response": "",
        "error": None,
    }

    logger.info("processing_message", message_preview=user_message[:60])
    result = await graph.ainvoke(initial_state)
    logger.info("message_processed", intent=result.get("current_intent"))
    return result
