"""Prompt templates for every Gemini use case.

Each builder returns ``(system_prompt, user_prompt)`` — a pair of strings
ready to feed into ``GeminiService.generate()`` or
``GeminiService.generate_structured()``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


_COACH_PERSONA = (
    "You are Coach J, an elite basketball shooting coach inside the SHOOTRZ app. "
    "You draw on sports-science research and NBA coaching methods. "
    "Be concise, encouraging, and actionable. Use bullet points when listing. "
    "Never invent numbers that aren't in the data provided. "
    "Speak in second person ('you') directly to the player."
)


# ------------------------------------------------------------------
# Chat
# ------------------------------------------------------------------

def build_chat_prompt(
    user_context: Dict[str, Any],
    messages: List[Dict[str, str]],
) -> str:
    """Return the system prompt for Coach J chat.  Messages are passed
    separately to the LLM as ``contents``.
    """
    context_json = json.dumps(user_context, ensure_ascii=False)
    return (
        f"{_COACH_PERSONA}\n"
        "You MUST personalize advice using the player data below.\n"
        "Rules:\n"
        "- Be concise and actionable. Prefer bullet points.\n"
        "- If the user asks about progress, reference trends from history.\n"
        "- If data is missing, ask 1 clarifying question.\n"
        "- When suggesting drills, give sets/reps and a 7-day plan.\n"
        "\n"
        "PLAYER_DATA_JSON:\n"
        f"{context_json}\n"
    )


# ------------------------------------------------------------------
# Shot Feedback (Phase 3)
# ------------------------------------------------------------------

def build_shot_feedback_prompt(
    metrics: List[Dict[str, Any]],
    score_components: List[Dict[str, Any]],
    overall_score: int,
    score_tier: str,
    user_profile: Optional[Dict[str, Any]] = None,
) -> tuple[str, str]:
    """Prompt for the holistic shot-feedback call.

    The 2026-04-23 pass reworked this so Gemini ALSO returns the user-facing
    ``ai_overall_score``. The backend's rule-based number (passed in as
    ``overall_score``) is a conservative geometric mean that collapses when
    any single axis is weak — it's meant to be a deterministic floor. The
    system prompt tells Gemini to grade like an amateur coach: reward
    attempted form, don't over-punish a single weak axis, and only collapse
    to < 30 when the motion doesn't look like a shot at all.
    """
    system = (
        f"{_COACH_PERSONA}\n"
        "You are reviewing a single basketball shot analyzed by computer vision. "
        "The angle values below are factual measurements — do NOT contradict them, "
        "but you DO decide the final holistic score.\n\n"
        "SCORING RUBRIC (output as ai_overall_score):\n"
        "  85-100 : textbook form across elbow, knee, and follow-through.\n"
        "  70-84  : solid jumpshot with minor issues on one axis (e.g. slightly bent "
        "           elbow ~150 deg, or slightly shallow knee ~85 deg).\n"
        "  55-69  : recognisable jumpshot with 1-2 real issues. An attempted shot "
        "           with one weak axis still belongs here - do NOT push it below 55.\n"
        "  35-54  : visible form problems on multiple axes but effort + intent are "
        "           clearly a jumpshot motion.\n"
        "  15-34  : motion barely resembles a shot; several core metrics are far from "
        "           target.\n"
        "   0-14  : unusable data (no real shot in frame, camera pointed wrong, etc).\n\n"
        "IMPORTANT:\n"
        " - Grade the ATTEMPTED motion, not the textbook ideal. A recreational shooter "
        "   whose elbow ends at 152 deg (target 165-180) and wrist follow-through at "
        "   26 deg (target 18-28) deserves a score in the 65-80 band, not sub-30.\n"
        " - The backend's rule-based score is deliberately harsh and often wrong; do "
        "   not anchor to it.\n"
        " - ai_score_rationale must cite the actual metric values (one sentence).\n"
        " - Provide natural, coach-style explanations for each metric, strengths, "
        "   improvements, feedback bullets, and optional drills.\n"
    )

    profile_str = ""
    if user_profile:
        profile_str = f"\nPlayer profile: {json.dumps(user_profile, ensure_ascii=False)}"

    user = (
        f"Backend rule-based score (reference only, often too harsh): {overall_score}/100 (tier: {score_tier})\n"
        f"Primitive metrics: {json.dumps(metrics, ensure_ascii=False)}\n"
        f"Score components: {json.dumps(score_components, ensure_ascii=False)}"
        f"{profile_str}\n\n"
        "Return the full structured response, including a holistic ai_overall_score "
        "graded per the rubric above."
    )
    return system, user


# ------------------------------------------------------------------
# Drill Recommendation (Phase 4)
# ------------------------------------------------------------------

def build_drill_recommendation_prompt(
    drill_metadata: Dict[str, Any],
    weak_areas: List[str],
    user_level: Optional[str] = None,
) -> tuple[str, str]:
    system = (
        f"{_COACH_PERSONA}\n"
        "You are explaining why a specific drill was recommended "
        "and how to perform it. Keep it brief and basketball-specific."
    )

    level_str = f"Player level: {user_level}\n" if user_level else ""
    user = (
        f"{level_str}"
        f"Weak areas to address: {', '.join(weak_areas) if weak_areas else 'general improvement'}\n"
        f"Selected drill: {json.dumps(drill_metadata, ensure_ascii=False)}\n\n"
        "Explain why this drill helps and how to do it."
    )
    return system, user


# ------------------------------------------------------------------
# Session Summary (Phase 5)
# ------------------------------------------------------------------

def build_session_summary_prompt(
    session_data: Dict[str, Any],
    history_summary: Optional[List[Dict[str, Any]]] = None,
) -> tuple[str, str]:
    system = (
        f"{_COACH_PERSONA}\n"
        "Summarize this training session in 2-3 sentences. "
        "Mention the score, what went well, and the #1 area to work on next. "
        "If previous sessions are given, note progress."
    )

    history_str = ""
    if history_summary:
        history_str = f"\nRecent session history: {json.dumps(history_summary, ensure_ascii=False)}"

    user = (
        f"Session data: {json.dumps(session_data, ensure_ascii=False)}"
        f"{history_str}\n\n"
        "Generate a session summary."
    )
    return system, user


# ------------------------------------------------------------------
# Progress Insight (Phase 5)
# ------------------------------------------------------------------

def build_progress_insight_prompt(
    stats: Dict[str, Any],
    recent_summaries: List[Dict[str, Any]],
) -> tuple[str, str]:
    system = (
        f"{_COACH_PERSONA}\n"
        "Analyze the player's recent performance trends. "
        "Call out specific improvements or regressions with numbers. "
        "End with one clear recommendation for the next session."
    )

    user = (
        f"Player stats: {json.dumps(stats, ensure_ascii=False)}\n"
        f"Recent sessions: {json.dumps(recent_summaries, ensure_ascii=False)}\n\n"
        "Generate a progress insight."
    )
    return system, user


# ------------------------------------------------------------------
# Metric Explanation (single metric)
# ------------------------------------------------------------------

def build_metric_explanation_prompt(
    metric_name: str,
    value: float,
    verdict: str,
    good_range: List[float],
    optimal_range: List[float],
) -> tuple[str, str]:
    system = (
        f"{_COACH_PERSONA}\n"
        "Explain a single shooting metric to a basketball player. "
        "Be specific about what the number means physically."
    )

    user = (
        f"Metric: {metric_name}\n"
        f"Value: {value}\n"
        f"Verdict: {verdict}\n"
        f"Good range: {good_range}\n"
        f"Optimal range: {optimal_range}\n\n"
        "Explain what this means for the player's shot."
    )
    return system, user


# ------------------------------------------------------------------
# Feedback Rules Rephrasing (Phase 6)
# ------------------------------------------------------------------

def build_feedback_rephrase_prompt(
    feedback_items: List[Dict[str, Any]],
) -> tuple[str, str]:
    system = (
        f"{_COACH_PERSONA}\n"
        "Rephrase the following rule-based feedback into natural, "
        "conversational coaching language. Keep the same severity and facts — "
        "just make the tone warmer and more motivating. "
        "Do NOT change or contradict any numbers or recommendations."
    )

    user = (
        f"Feedback items: {json.dumps(feedback_items, ensure_ascii=False)}\n\n"
        "Rephrase each item."
    )
    return system, user
