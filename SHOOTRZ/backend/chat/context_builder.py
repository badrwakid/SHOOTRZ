from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..storage.db import db


@dataclass(frozen=True)
class ContextBuildOptions:
    include_raw_artifacts: bool = False
    max_recent_summaries: int = 5
    max_chat_history: int = 20


def _score_tier(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 90:
        return "elite"
    if score >= 75:
        return "great"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def build_user_context(
    *,
    user_id: str,
    user_local_context: Optional[Dict[str, Any]],
    options: ContextBuildOptions,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build a compact context object for Coach J.

    Uses server-side Supabase data (analysis_summaries, user_profiles,
    user_streaks) instead of raw video/metric trees. This prevents the
    Gemini 429 token explosion that occurred when full MVP payloads were
    sent in the system prompt.
    """
    user = db.get_user(user_id)
    profile = db.get_user_profile(user_id)
    stats = db.get_user_stats(user_id)
    summaries = db.get_recent_summaries(user_id, limit=options.max_recent_summaries)

    user_section: Dict[str, Any] = {}
    if user:
        user_section = {
            "name": user.get("name"),
            "skill_level": user.get("skill_level"),
            "position": user.get("position"),
            "dominant_hand": user.get("dominant_hand"),
        }
    if profile:
        user_section["coaching_style"] = profile.get("coaching_style", "balanced")
        user_section["primary_goal"] = profile.get("primary_goal")
        user_section["training_frequency"] = profile.get("training_frequency")
        user_section["years_playing"] = profile.get("years_playing")

    recent_sessions: List[Dict[str, Any]] = []
    for s in summaries:
        recent_sessions.append({
            "date": s.get("created_at"),
            "overall_score": s.get("overall_score"),
            "score_tier": s.get("score_tier") or _score_tier(s.get("overall_score")),
            "top_improvements": (s.get("top_improvements") or [])[:3],
            "top_strengths": (s.get("top_strengths") or [])[:3],
        })

    goals: List[str] = []
    if user and user.get("goals"):
        goals = user["goals"][:10]
    if isinstance(user_local_context, dict):
        local_goals = user_local_context.get("goals")
        if isinstance(local_goals, list) and not goals:
            goals = [
                g.get("title", str(g)) if isinstance(g, dict) else str(g)
                for g in local_goals[:10]
            ]

    primary_goal = profile.get("primary_goal") if profile else None

    context: Dict[str, Any] = {
        "user": user_section,
        "stats": stats if isinstance(stats, dict) else {},
        "recent_sessions": recent_sessions,
        "goals": goals,
        "primary_goal": primary_goal,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    context_used = {
        "profile": bool(user),
        "user_profile": bool(profile),
        "recent_summaries_count": len(recent_sessions),
        "stats_available": bool(stats),
        "has_client_local_context": bool(user_local_context),
        "include_raw_artifacts": options.include_raw_artifacts,
    }

    return context, context_used


def sanitize_context_for_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the context is within safe size bounds for the LLM prompt."""
    out = copy.deepcopy(context)

    sessions = out.get("recent_sessions")
    if isinstance(sessions, list):
        out["recent_sessions"] = sessions[:5]

    goals = out.get("goals")
    if isinstance(goals, list):
        out["goals"] = goals[:10]

    return out
