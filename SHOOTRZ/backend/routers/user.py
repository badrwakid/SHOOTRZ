"""User profile, stats, streak, drill, and workout endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..storage.db import db
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user

router = APIRouter(prefix="/api", tags=["user"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ProfileUpdateRequest(BaseModel):
    primary_goal: Optional[str] = None
    training_frequency: Optional[str] = None
    preferred_drill_duration: Optional[int] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    dominant_hand: Optional[str] = None
    years_playing: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    coaching_style: Optional[str] = None


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
    result = db.upsert_user_profile(user.user_id, data)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update profile")
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
