from typing import Any, Dict, List, Optional

from .supabase_client import get_service_client


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
	sb = get_service_client()
	resp = (
		sb.table("users")
		.select("id, email, username, name, skill_level, position, auth_provider, has_completed_onboarding, created_at")
		.eq("id", user_id)
		.maybe_single()
		.execute()
	)
	return resp.data or None


def record_video(user_id: str, file_url: str, angle: Optional[str], fps: Optional[int], device: Optional[str]) -> str:
    sb = get_service_client()
    resp = sb.table("videos").insert({
        "user_id": user_id,
        "file_url": file_url,
        "angle": angle,
        "fps": fps,
        "device": device,
    }).execute()
    return resp.data[0]["id"]


def record_metrics(video_id: str, metrics: List[Dict[str, Any]]) -> List[str]:
    if not metrics:
        return []
    sb = get_service_client()
    rows = [
        {
            "video_id": video_id,
            "metric_name": m["metric_name"],
            "value": float(m["value"]),
            "confidence": float(m.get("confidence", 0.0)),
        }
        for m in metrics
    ]
    resp = sb.table("metrics").insert(rows).execute()
    return [row["id"] for row in (resp.data or [])]


def record_feedback(items: List[Dict[str, Any]]) -> List[str]:
    if not items:
        return []
    sb = get_service_client()
    resp = sb.table("feedback").insert(items).execute()
    return [row["id"] for row in (resp.data or [])]


def get_user_history(user_id: str) -> List[Dict[str, Any]]:
	sb = get_service_client()
	resp = (
		sb.table("videos")
		.select("id, created_at, angle, fps, device, file_url, recorded_at, camera_angle")
		.eq("user_id", user_id)
		.order("created_at", desc=True)
		.execute()
	)
	return resp.data or []


def get_video_metrics(video_id: str) -> List[Dict[str, Any]]:
	"""Get all metrics for a video."""
	sb = get_service_client()
	resp = (
		sb.table("metrics")
		.select("id, metric_name, value, unit, confidence, phase, frame_idx, created_at")
		.eq("video_id", video_id)
		.order("created_at", desc=False)
		.execute()
	)
	return resp.data or []


def get_video_feedback(video_id: str) -> List[Dict[str, Any]]:
	"""Get all feedback for a video (via metrics)."""
	sb = get_service_client()
	resp = (
		sb.table("feedback")
		.select("id, metric_id, message, severity, created_at")
		.in_("metric_id", 
			sb.table("metrics")
			.select("id")
			.eq("video_id", video_id)
		)
		.execute()
	)
	return resp.data or []


def create_session(user_id: str, title: Optional[str] = None, date: Optional[str] = None) -> str:
	"""Create a new practice session."""
	sb = get_service_client()
	data = {"user_id": user_id}
	if title:
		data["title"] = title
	if date:
		data["date"] = date
	resp = sb.table("sessions").insert(data).execute()
	return resp.data[0]["id"] if resp.data else ""


def add_video_to_session(session_id: str, video_id: str) -> bool:
	"""Add a video to a session."""
	sb = get_service_client()
	try:
		resp = sb.table("session_videos").insert({
			"session_id": session_id,
			"video_id": video_id,
		}).execute()
		return True
	except Exception as e:
		print(f"Error adding video to session: {e}")
		return False


def get_session_videos(session_id: str) -> List[Dict[str, Any]]:
	"""Get all videos in a session."""
	sb = get_service_client()
	resp = (
		sb.table("session_videos")
		.select("video_id, videos(*)")
		.eq("session_id", session_id)
		.execute()
	)
	return resp.data or []






