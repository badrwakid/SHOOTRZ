"""User profile, stats, streak, drill, workout, and progress insight endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..contracts.history import HISTORY_API_SOURCE, HistoryResponse, session_from_db_row
from ..services.llm import llm_service
from ..storage.db import db
from ..storage.supabase_client import get_service_client
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["user"])

USERS_CORE_FIELDS = {
    "name",
    "username",
    "skill_level",
    "position",
    "has_completed_onboarding",
}

USER_PROFILE_FIELDS = {
    "bio",
    "avatar_url",
    "primary_goal",
    "training_frequency",
    "preferred_drill_duration",
    "age",
    "height_cm",
    "weight_kg",
    "dominant_hand",
    "years_playing",
    "notifications_enabled",
    "dark_mode_enabled",
    "analytics_enabled",
    "coaching_style",
}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    skill_level: Optional[str] = None
    position: Optional[str] = None
    has_completed_onboarding: Optional[bool] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    primary_goal: Optional[str] = None
    training_frequency: Optional[str] = None
    preferred_drill_duration: Optional[int] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    dominant_hand: Optional[str] = None
    years_playing: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    dark_mode_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None
    coaching_style: Optional[str] = None


class UserPreferencesRequest(BaseModel):
    notifications_enabled: Optional[bool] = None
    dark_mode_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None


class DrillCompleteRequest(BaseModel):
    drill_id: str
    drill_name: str
    duration_seconds: Optional[int] = None
    user_rating: Optional[int] = None
    notes: Optional[str] = None


class WorkoutProgressUpdateRequest(BaseModel):
    workout_name: str
    status: Optional[str] = None
    drills_completed: Optional[int] = None
    drills_total: Optional[int] = None


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@router.get("/user/profile")
async def get_user_profile(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    base = db.get_user(user.user_id)
    profile = db.get_user_profile(user.user_id)
    if not base:
        raise HTTPException(status_code=404, detail="User not found")
    merged: Dict[str, Any] = {**(base or {}), "profile": profile}
    return merged


@router.put("/user/profile")
async def update_user_profile(
    body: ProfileUpdateRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=422, detail="No fields to update")

    core_fields = {k: v for k, v in data.items() if k in USERS_CORE_FIELDS}
    profile_fields = {k: v for k, v in data.items() if k in USER_PROFILE_FIELDS}

    result = db.update_user_full_atomic(
        user_id=user.user_id,
        core_fields=core_fields,
        profile_fields=profile_fields,
    )
    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile atomically",
        )
    # Keep PUT shape coherent with GET /api/user/profile.
    base = db.get_user(user.user_id)
    profile = db.get_user_profile(user.user_id)
    if not base:
        raise HTTPException(status_code=404, detail="User not found")
    return {**(base or {}), "profile": profile}


@router.put("/user/preferences")
async def update_user_preferences(
    body: UserPreferencesRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=422, detail="No preference fields to update")
    result = db.upsert_user_profile(user.user_id, data)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update preferences")
    base = db.get_user(user.user_id)
    if not base:
        raise HTTPException(status_code=404, detail="User not found")
    return {**(base or {}), "profile": result}


@router.get("/user/export")
async def export_user_data(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    result = db.build_user_export_payload(
        user_id=user.user_id,
        sessions_limit=100,
        chat_messages_limit=200,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to export user data")
    return result


# ---------------------------------------------------------------------------
# Stats / Streak
# ---------------------------------------------------------------------------

@router.get("/user/stats")
async def get_user_stats(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    stats = db.get_user_stats(user.user_id)
    return stats


@router.get("/user/streak")
async def get_user_streak(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    streak = db.get_streak(user.user_id)
    if not streak:
        return {"current_streak": 0, "longest_streak": 0, "last_activity_date": None}
    return streak


@router.get("/user/progress-insight")
async def get_progress_insight(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Gemini-powered trend analysis of recent performance."""
    stats = db.get_user_stats(user.user_id)
    summaries = db.get_recent_summaries(user.user_id, limit=10)

    if not summaries:
        return {
            "insight": "Record your first session to get personalized progress insights.",
            "highlights": [],
            "next_focus": "Start by recording a shot video for analysis.",
        }

    compact_summaries = [
        {
            "date": s.get("created_at"),
            "overall_score": s.get("overall_score"),
            "score_tier": s.get("score_tier"),
            "top_strengths": (s.get("top_strengths") or [])[:2],
            "top_improvements": (s.get("top_improvements") or [])[:2],
        }
        for s in summaries
    ]

    result = llm_service.get_progress_insight(
        stats=stats if isinstance(stats, dict) else {},
        recent_summaries=compact_summaries,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.get("/sessions")
async def get_sessions(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = 20,
    offset: int = 0,
):
    sessions = db.get_user_sessions(user.user_id, limit=limit, offset=offset)
    return {"sessions": sessions, "count": len(sessions)}


@router.get("/user/analysis-history", response_model=HistoryResponse)
async def get_analysis_history(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """MVP shot history: sessions + analysis_summaries + metrics (authenticated)."""
    try:
        raw = db.get_user_analysis_history(
            user.user_id, limit=limit, offset=offset,
        )
        logger.info(
            "history_query",
            extra={
                "user_id": user.user_id,
                "history_source": HISTORY_API_SOURCE,
                "limit": limit,
                "offset": offset,
                "history_rows": len(raw),
            },
        )
        return HistoryResponse(
            user_id=user.user_id,
            sessions=[session_from_db_row(s) for s in raw],
            total=len(raw),
            limit=limit,
            offset=offset,
            source=HISTORY_API_SOURCE,
        )
    except Exception as exc:
        logger.exception("get_analysis_history failed", extra={"user_id": user.user_id})
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    summary = None
    summaries = db.get_recent_summaries(user.user_id, limit=100)
    for s in summaries:
        if s.get("session_id") == session_id:
            summary = s
            break
    return {**session, "summary": summary}


# ---------------------------------------------------------------------------
# Drills
# ---------------------------------------------------------------------------

@router.get("/drills/completions")
async def get_drill_completions(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = 50,
):
    completions = db.get_drill_completions(user.user_id, limit=limit)
    return {"completions": completions, "count": len(completions)}


@router.post("/drills/complete")
async def complete_drill(
    body: DrillCompleteRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    result = db.save_drill_completion(user.user_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to save drill completion")
    db.update_streak(user.user_id)
    return result


# ---------------------------------------------------------------------------
# Workouts
# ---------------------------------------------------------------------------

@router.get("/workouts/progress")
async def get_workout_progress(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    progress = db.get_workout_progress(user.user_id)
    return {"workouts": progress, "count": len(progress)}


@router.put("/workouts/{workout_id}/progress")
async def update_workout_progress(
    workout_id: str,
    body: WorkoutProgressUpdateRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    data = body.model_dump(exclude_none=True)
    result = db.upsert_workout_progress(user.user_id, workout_id, data)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update workout progress")
    return result


# ---------------------------------------------------------------------------
# Account deletion (service role — public data + Auth admin)
# ---------------------------------------------------------------------------


@router.delete("/user/account")
async def delete_user_account(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Delete all app data for the user, then remove the Auth user."""
    uid = user.user_id
    if not db.delete_all_data_for_user(uid):
        logger.error("delete_all_data_for_user returned false", extra={"user_id": uid})
        raise HTTPException(status_code=500, detail="Failed to delete user data")
    try:
        get_service_client().auth.admin.delete_user(uid)
    except Exception as exc:
        logger.exception(
            "auth.admin.delete_user failed after public data removed",
            extra={"user_id": uid},
        )
        raise HTTPException(
            status_code=502,
            detail="Stored data was removed but auth deletion failed. Contact support.",
        ) from exc
    logger.info("user account deleted", extra={"user_id": uid})
    return {"status": "deleted", "user_id": uid}
