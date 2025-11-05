"""
Session management endpoints.

Create sessions, add videos to sessions, retrieve session data.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from ..storage.db import (
	create_session,
	add_video_to_session,
	get_session_videos,
	get_user_history,
)
from ..utils.validation import validate_user_id


router = APIRouter(prefix="", tags=["sessions"])


class CreateSessionRequest(BaseModel):
	title: Optional[str] = None
	date: Optional[str] = None


class SessionResponse(BaseModel):
	id: str
	user_id: str
	title: Optional[str]
	date: Optional[str]
	video_count: int


@router.post("/sessions/{user_id}")
async def create_session_endpoint(
	user_id: str,
	request: CreateSessionRequest,
):
	"""Create a new practice session."""
	is_valid, error = validate_user_id(user_id)
	if not is_valid:
		raise HTTPException(status_code=400, detail=error)

	try:
		session_id = create_session(
			user_id=user_id,
			title=request.title,
			date=request.date,
		)
		return {"session_id": session_id, "status": "created"}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/sessions/{session_id}/videos/{video_id}")
async def add_video_to_session_endpoint(session_id: str, video_id: str):
	"""Add a video to a session."""
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
	"""Get session details with videos and metrics."""
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
	"""Get all sessions for a user."""
	is_valid, error = validate_user_id(user_id)
	if not is_valid:
		raise HTTPException(status_code=400, detail=error)

	try:
		# Get all videos for user (each video can be a session)
		videos = get_user_history(user_id)
		
		# Group by date to form sessions
		sessions = {}
		for video in videos:
			video_date = video["created_at"][:10]  # YYYY-MM-DD
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
