"""
LangGraph state definition — the shared data structure flowing through all agents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class UserContext(TypedDict, total=False):
    """Contextual info about the user, pulled from DB before agent invocation."""
    user_id: str
    phone_number: str
    display_name: Optional[str]
    timezone: str
    current_streak: int
    longest_streak: int
    consistency_score: float
    total_xp: int
    level: int
    dormant_mode: bool
    pending_tasks_today: List[Dict[str, Any]]
    active_goals: List[Dict[str, Any]]
    recent_completion_rate: float


class ExtractedTask(TypedDict, total=False):
    """A task extracted by the Planner from natural language."""
    description: str
    category: str
    difficulty: str
    priority: str
    scheduled_date: str  # ISO format
    scheduled_time: Optional[str]
    estimated_minutes: Optional[int]
    goal_title: Optional[str]  # If user references a goal


class TaskModification(TypedDict, total=False):
    """A modification to an existing task, extracted by the Tracker."""
    task_id: str
    task_description: str
    new_status: str  # completed | missed | rescheduled
    reschedule_date: Optional[str]
    notes: Optional[str]


class GraphState(TypedDict, total=False):
    """The complete state object that flows through the LangGraph pipeline."""

    # ── Conversation ─────────────────────────────────────────────────────
    messages: List[BaseMessage]
    user_message: str  # Raw incoming message from WhatsApp

    # ── Routing ──────────────────────────────────────────────────────────
    current_intent: str
    # Possible intents:
    #   scheduling     — user wants to add/plan tasks
    #   status_update  — user responding to night check or marking tasks done
    #   goal_setting   — user setting long-term goals
    #   query          — user asking about their tasks/progress
    #   weekly_report  — triggered by scheduler for weekly summary
    #   general_chat   — casual conversation / unclear intent
    #   help           — user asking for help with the bot

    # ── User Context ─────────────────────────────────────────────────────
    user_context: UserContext

    # ── Agent Outputs ────────────────────────────────────────────────────
    extracted_tasks: List[ExtractedTask]
    task_modifications: List[TaskModification]
    goal_data: Optional[Dict[str, Any]]

    # ── Response ─────────────────────────────────────────────────────────
    response: str  # Final message to send back to user
    error: Optional[str]
