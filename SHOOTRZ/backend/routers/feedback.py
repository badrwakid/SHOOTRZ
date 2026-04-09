"""
Feedback endpoints for retrieving and managing feedback.
"""

from fastapi import APIRouter, HTTPException


from ..storage.db import get_video_feedback, get_video_metrics
from ..feedback.engine import generate_feedback


router = APIRouter(prefix="", tags=["feedback"])


@router.get("/feedback/video/{video_id}")
async def get_video_feedback_endpoint(video_id: str):
	"""
	Get all feedback for a video.
	
	Args:
		video_id: Video ID
	
	Returns:
		List of feedback items
	"""
	try:
		feedback = get_video_feedback(video_id)
		return {
			"video_id": video_id,
			"feedback": feedback,
			"count": len(feedback),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error fetching feedback: {str(e)}")


@router.post("/feedback/generate")
async def generate_feedback_endpoint(video_id: str):
	"""
	Generate feedback from video metrics (if not already generated).
	
	Args:
		video_id: Video ID
	
	Returns:
		Generated feedback list
	"""
	try:
		metrics = get_video_metrics(video_id)
		if not metrics:
			raise HTTPException(status_code=404, detail="No metrics found for video")
		
		feedback = generate_feedback(metrics)
		return {
			"video_id": video_id,
			"feedback": feedback,
			"count": len(feedback),
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error generating feedback: {str(e)}")
