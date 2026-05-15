from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..storage.supabase_client import get_service_client

logger = logging.getLogger(__name__)

_PROMPT_SAFE_RE = re.compile(r"[^\w\s.,!?'\"\\():;\-]")


def _sanitize_str(s: object, max_len: int = 200) -> str:
    """Strip non-printable and injection-prone characters from user-supplied strings."""
    if s is None:
        return ""
    if not isinstance(s, str):
        return str(s)[:max_len]
    return _PROMPT_SAFE_RE.sub("", s)[:max_len]

MAX_CONTEXT_CHARS = 32_000


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


def _classify_rpc_fallback_reason(exc: Exception) -> str:
    msg = str(exc).lower()
    if "service_client_unavailable" in msg:
        return "service_client_unavailable"
    if (
        "get_coach_context" in msg
        and ("does not exist" in msg or "undefined function" in msg or "42883" in msg)
    ):
        return "missing_get_coach_context"
    return "rpc_get_coach_context_failed"


def _build_context_via_direct_queries(
    *,
    sb: Any,
    user_id: str,
    summary_limit: int,
    chat_limit: int,
) -> Dict[str, Any]:
    """Best-effort fallback path when get_coach_context RPC is unavailable."""
    out: Dict[str, Any] = {}
    try:
        user_resp = (
            sb.table("users")
            .select("id, name, skill_level, position")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        out["user"] = user_resp.data or {}
    except Exception:
        logger.exception("context fallback: users query failed", extra={"user_id": user_id})
        out["user"] = {}

    try:
        profile_resp = (
            sb.table("user_profiles")
            .select("coaching_style, primary_goal, training_frequency, years_playing, dominant_hand")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        out["profile"] = profile_resp.data or {}
    except Exception:
        logger.exception("context fallback: user_profiles query failed", extra={"user_id": user_id})
        out["profile"] = {}

    try:
        summaries_resp = (
            sb.table("analysis_summaries")
            .select("created_at, overall_score, score_tier, top_improvements, top_strengths")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(max(1, int(summary_limit)))
            .execute()
        )
        out["summaries"] = summaries_resp.data or []
    except Exception:
        logger.exception("context fallback: analysis_summaries query failed", extra={"user_id": user_id})
        out["summaries"] = []

    try:
        chat_resp = (
            sb.table("chat_history")
            .select("role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(max(1, int(chat_limit)))
            .execute()
        )
        # Keep chronological order for conversational continuity.
        out["recent_chat"] = list(reversed(chat_resp.data or []))
    except Exception:
        logger.exception("context fallback: chat_history query failed", extra={"user_id": user_id})
        out["recent_chat"] = []

    # Keep this optional/empty to remain backward-compatible with prior context.
    out["stats"] = {}
    return out


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
    summary_limit = getattr(options, "max_recent_summaries", 5) if options else 5

    rpc_fallback_reason: Optional[str] = None
    try:
        sb = get_service_client()
    except Exception:
        logger.exception("build_user_context: service client unavailable", extra={"user_id": user_id})
        sb = None

    try:
        if sb is None:
            raise RuntimeError("service_client_unavailable")
        resp = sb.rpc(
            "get_coach_context",
            {"p_user_id": user_id, "p_summary_limit": summary_limit},
        ).execute()
        ctx_data = resp.data or {}
    except Exception as exc:
        rpc_fallback_reason = _classify_rpc_fallback_reason(exc)
        logger.exception(
            "build_user_context: RPC get_coach_context failed; using direct-query fallback",
            extra={"user_id": user_id, "fallback_reason": rpc_fallback_reason},
        )
        if sb is None:
            ctx_data = {}
        else:
            chat_limit = getattr(options, "max_chat_history", 20) if options else 20
            ctx_data = _build_context_via_direct_queries(
                sb=sb,
                user_id=user_id,
                summary_limit=summary_limit,
                chat_limit=chat_limit,
            )
    user = ctx_data.get("user") or {}
    profile = ctx_data.get("profile") or {}
    stats = ctx_data.get("stats") or {}
    summaries = ctx_data.get("summaries") or []
    recent_chat_raw = ctx_data.get("recent_chat") or []

    if not summaries:
        logger.info(
            "build_user_context: no analysis_summaries rows for user",
            extra={"user_id": user_id},
        )

    user_section: Dict[str, Any] = {}
    if user:
        user_section = {
            "name": _sanitize_str(user.get("name"), max_len=80),
            "skill_level": _sanitize_str(user.get("skill_level"), max_len=50),
            "position": _sanitize_str(user.get("position"), max_len=50),
            # Canonical schema: dominant_hand lives on user_profiles, not public.users.
            "dominant_hand": user.get("dominant_hand") or profile.get("dominant_hand"),
        }
    if profile:
        user_section["coaching_style"] = _sanitize_str(profile.get("coaching_style", "balanced"), max_len=80)
        user_section["primary_goal"] = _sanitize_str(profile.get("primary_goal"), max_len=300)
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

    primary_goal = _sanitize_str(profile.get("primary_goal"), max_len=300) if profile else None

    context: Dict[str, Any] = {
        "user": user_section,
        "stats": stats if isinstance(stats, dict) else {},
        "recent_sessions": recent_sessions,
        "recent_chat": recent_chat_raw if isinstance(recent_chat_raw, list) else [],
        "goals": goals,
        "primary_goal": primary_goal,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    context_used = {
        "profile": bool(user),
        "user_profile": bool(profile),
        "recent_summaries_count": len(recent_sessions),
        "recent_chat_count": len(context["recent_chat"]),
        "stats_available": bool(stats),
        "has_client_local_context": bool(user_local_context),
        "include_raw_artifacts": options.include_raw_artifacts,
    }
    if rpc_fallback_reason:
        context_used["rpc_fallback_reason"] = rpc_fallback_reason

    return context, context_used


def sanitize_context_for_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the context is within safe size bounds for the LLM prompt."""
    out = copy.deepcopy(context)

    sessions = out.get("recent_sessions")
    if isinstance(sessions, list):
        out["recent_sessions"] = sessions[:5]
    recent_chat = out.get("recent_chat")
    if isinstance(recent_chat, list):
        out["recent_chat"] = recent_chat[-20:]

    goals = out.get("goals")
    if isinstance(goals, list):
        out["goals"] = goals[:10]

    # Hard cap: trim until serialized JSON is within MAX_CONTEXT_CHARS
    if len(json.dumps(out, default=str)) > MAX_CONTEXT_CHARS:
        # Phase 1: pop recent_sessions one at a time from the end
        sessions = out.get("recent_sessions")
        while isinstance(sessions, list) and sessions and len(json.dumps(out, default=str)) > MAX_CONTEXT_CHARS:
            sessions.pop()

        # Phase 2: if still over limit, truncate large string fields
        if len(json.dumps(out, default=str)) > MAX_CONTEXT_CHARS:
            _LARGE_STRING_FIELDS = ["stats", "user", "primary_goal"]
            for field in _LARGE_STRING_FIELDS:
                val = out.get(field)
                if isinstance(val, str) and len(val) > 500:
                    out[field] = val[:500]
                elif isinstance(val, dict):
                    # Truncate any oversized string values within the dict
                    for k, v in val.items():
                        if isinstance(v, str) and len(v) > 200:
                            val[k] = v[:200]
                if len(json.dumps(out, default=str)) <= MAX_CONTEXT_CHARS:
                    break

        # Phase 3: last resort — return a minimal safe fallback
        if len(json.dumps(out, default=str)) > MAX_CONTEXT_CHARS:
            logger.warning(
                "sanitize_context_for_llm: context still over limit after trimming; "
                "returning minimal fallback",
                extra={"size": len(json.dumps(out, default=str))},
            )
            return {
                "user": out.get("user", {}),
                "stats": {},
                "recent_sessions": [],
                "recent_chat": [],
                "goals": [],
                "primary_goal": None,
                "generated_at": out.get("generated_at"),
                "_truncated": True,
            }

    return out
