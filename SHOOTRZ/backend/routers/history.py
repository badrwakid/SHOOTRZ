import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

from ..contracts.history import HistoryResponse, HistoryStatsResponse
from ..storage.db import get_user_history, get_video_metrics
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user


router = APIRouter(prefix="", tags=["history"])
logger = logging.getLogger(__name__)


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def history(
	user_id: str,
	user: AuthenticatedUser = Depends(get_authenticated_user),
	limit: Optional[int] = 50,
	offset: Optional[int] = 0,
	start_date: Optional[str] = None,
	end_date: Optional[str] = None,
):
	"""
	Get user's analysis history with sessions and aggregated metrics.

	Deprecated for clients: prefer ``GET /api/user/analysis-history`` with a
	Bearer token (user-scoped, correct MVP scores from analysis_summaries).
	This endpoint is unauthenticated and uses legacy video rows only.
	"""
	if user.user_id != user_id:
		raise HTTPException(status_code=403, detail="Cannot access another user's history")
	try:
		logger.warning(
			"legacy /history/%s used — prefer GET /api/user/analysis-history",
			user_id,
		)
		videos = get_user_history(user_id)
		
		# Apply date filtering
		if start_date:
			start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
			videos = [v for v in videos if datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')) >= start_dt]
		
		if end_date:
			end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
			videos = [v for v in videos if datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')) <= end_dt]
		
		# Apply pagination
		total = len(videos)
		videos = videos[offset:offset + limit] if limit else videos[offset:]
		
		# Build sessions with metrics
		sessions = []
		for video in videos:
			video_id = video["id"]
			metrics = get_video_metrics(video_id)
			
			# Calculate average score from metrics
			avg_score = None
			if metrics:
				values = [m.get("value", 0) for m in metrics if m.get("value") is not None]
				if values:
					avg_score = sum(values) / len(values)
			
			sessions.append({
				"session_id": video_id,
				"timestamp": video["created_at"],
				"title": None,
				"date": video["created_at"][:10],
				"shot_count": 1,
				"average_score": avg_score,
				"metrics": metrics,
				"angle": video.get("camera_angle"),
				"fps": video.get("fps"),
				"device": None,
			})
		
		return {
			"user_id": user_id,
			"sessions": sessions,
			"total": total,
			"limit": limit,
			"offset": offset,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@router.get("/history/{user_id}/stats", response_model=HistoryStatsResponse)
async def get_history_stats(
	user_id: str,
	user: AuthenticatedUser = Depends(get_authenticated_user),
):
	"""
	Get aggregated statistics from user's history.

	Returns total sessions, average scores, improvement trends, etc.
	"""
	if user.user_id != user_id:
		raise HTTPException(status_code=403, detail="Cannot access another user's history")
	try:
		videos = get_user_history(user_id)
		
		if not videos:
			return {
				"total_sessions": 0,
				"total_shots": 0,
				"average_score": None,
				"best_score": None,
				"improvement_percentage": None,
				"consistency_score": None,
			}
		
		# Collect all metrics across videos
		all_metrics = []
		for video in videos:
			metrics = get_video_metrics(video["id"])
			if metrics:
				all_metrics.extend(metrics)
		
		if not all_metrics:
			return {
				"total_sessions": len(videos),
				"total_shots": len(videos),
				"average_score": None,
				"best_score": None,
				"improvement_percentage": None,
				"consistency_score": None,
			}
		
		# Calculate statistics
		metric_values = [m.get("value", 0) for m in all_metrics if m.get("value") is not None]
		average_score = sum(metric_values) / len(metric_values) if metric_values else None
		best_score = max(metric_values) if metric_values else None
		
		# Calculate improvement (compare first half vs second half)
		improvement_percentage = None
		if len(videos) >= 4:
			midpoint = len(videos) // 2
			first_half = videos[:midpoint]
			second_half = videos[midpoint:]
			
			first_metrics = []
			second_metrics = []
			for v in first_half:
				first_metrics.extend(get_video_metrics(v["id"]) or [])
			for v in second_half:
				second_metrics.extend(get_video_metrics(v["id"]) or [])
			
			if first_metrics and second_metrics:
				first_avg = sum(m.get("value", 0) for m in first_metrics) / len(first_metrics)
				second_avg = sum(m.get("value", 0) for m in second_metrics) / len(second_metrics)
				if first_avg > 0:
					improvement_percentage = ((second_avg - first_avg) / first_avg) * 100
		
		# Calculate consistency (inverse of coefficient of variation)
		consistency_score = None
		if metric_values and len(metric_values) > 1:
			mean = sum(metric_values) / len(metric_values)
			variance = sum((v - mean) ** 2 for v in metric_values) / len(metric_values)
			std_dev = variance ** 0.5
			if mean != 0:
				cv = std_dev / abs(mean)
				consistency_score = max(0, min(100, 100 * (1 - cv)))
		
		return {
			"total_sessions": len(videos),
			"total_shots": len(videos),
			"average_score": round(average_score, 2) if average_score is not None else None,
			"best_score": round(best_score, 2) if best_score is not None else None,
			"improvement_percentage": round(improvement_percentage, 2) if improvement_percentage is not None else None,
			"consistency_score": round(consistency_score, 2) if consistency_score is not None else None,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


