from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any

from ..utils.schemas import ResultResponse
from ..storage.local_cache import job_store
from ..storage.db import get_video_metrics, get_video_feedback


router = APIRouter(prefix="", tags=["results"])


@router.get("/result/{job_id}")
async def get_result(job_id: str):
	"""
	Get analysis result for a job.
	
	Returns metrics, feedback, phases, and processing status.
	"""
	if job_id not in job_store:
		raise HTTPException(status_code=404, detail="Job not found")

	job = job_store[job_id]
	status = job.get("status", "unknown")

	# If completed and video_id exists, fetch from database
	video_id = job.get("video_id")
	if status == "completed" and video_id:
		try:
			# Get metrics from database
			metrics = get_video_metrics(video_id)
			# Get feedback from database
			feedback = get_video_feedback(video_id)
			
			# Merge with job store data (which has phases)
			return {
				"job_id": job_id,
				"status": status,
				"video_id": video_id,
				"metrics": metrics or job.get("metrics", []),
				"feedback": feedback or job.get("feedback", []),
				"phases": job.get("phases", []),
				"pose_results": job.get("pose_results", 0),
				"hand_results": job.get("hand_results", 0),
				"ball_trajectory_length": job.get("ball_trajectory_length", 0),
			}
		except Exception as e:
			print(f"Error fetching from database: {e}")
			# Fallback to job store

	return {
		"job_id": job_id,
		"status": status,
		"metrics": job.get("metrics", []),
		"feedback": job.get("feedback", []),
		"phases": job.get("phases", []),
		"video_id": job.get("video_id"),
		"pose_results": job.get("pose_results", 0),
		"hand_results": job.get("hand_results", 0),
		"ball_trajectory_length": job.get("ball_trajectory_length", 0),
		"error": job.get("error"),
	}


@router.get("/result/{job_id}/status")
async def get_job_status(job_id: str):
	"""Get only the status of a job (lighter endpoint for polling)."""
	if job_id not in job_store:
		raise HTTPException(status_code=404, detail="Job not found")
	
	return {
		"job_id": job_id,
		"status": job_store[job_id].get("status", "unknown"),
	}






