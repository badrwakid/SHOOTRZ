"""Session management endpoints.

Create sessions, add videos to sessions, retrieve session data.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from pydantic import BaseModel

from ..storage.db import (
    create_session,
    add_video_to_session,
    get_session_videos,
    get_user_history,
)
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user
from ..utils.validation import validate_user_id


router = APIRouter(prefix="", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.post("/sessions/{user_id}")
async def create_session_endpoint(
    user_id: str,
    request: CreateSessionRequest,
):
    is_valid, error = validate_user_id(user_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    try:
        session_id = create_session(
            user_id=user_id,
            title=request.title,
        )
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/sessions/{session_id}/videos/{video_id}")
async def add_video_to_session_endpoint(session_id: str, video_id: str):
    try:
        success = add_video_to_session(session_id, video_id)
        if success:
            return {"status": "success", "message": "Video added to session"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add video to session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        videos = get_session_videos(session_id)
        return {
            "session_id": session_id,
            "videos": videos,
            "video_count": len(videos),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@router.get("/sessions/user/{user_id}")
async def get_user_sessions(user_id: str):
    is_valid, error = validate_user_id(user_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    try:
        videos = get_user_history(user_id)

        sessions = {}
        for video in videos:
            video_date = video["created_at"][:10]
            if video_date not in sessions:
                sessions[video_date] = {
                    "id": f"session_{video_date}",
                    "date": video_date,
                    "videos": [],
                }
            sessions[video_date]["videos"].append(video)

        return {
            "user_id": user_id,
            "sessions": list(sessions.values()),
            "total": len(sessions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")
