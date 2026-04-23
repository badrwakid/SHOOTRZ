from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .supabase_client import get_service_client

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Centralized database access layer.

    All methods use the service_role client (bypasses RLS) because the
    backend is a trusted server process. Every write uses upsert or
    ON CONFLICT patterns where applicable.
    """

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("users")
                .select("*")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            return resp.data or None
        except Exception:
            logger.exception("get_user failed", extra={"user_id": user_id})
            return None

    def upsert_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("users")
                .upsert(user_data, on_conflict="id")
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("upsert_user failed", extra={"user_id": user_data.get("id")})
            return None

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            return resp.data or None
        except Exception:
            logger.exception("get_user_profile failed", extra={"user_id": user_id})
            return None

    def upsert_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            profile_data["user_id"] = user_id
            resp = (
                sb.table("user_profiles")
                .upsert(profile_data, on_conflict="user_id")
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("upsert_user_profile failed", extra={"user_id": user_id})
            return None

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            sb = get_service_client()
            resp = sb.rpc("get_user_stats", {"p_user_id": user_id}).execute()
            return resp.data if resp.data else {}
        except Exception:
            logger.exception("get_user_stats failed", extra={"user_id": user_id})
            return {}

    # ------------------------------------------------------------------
    # Session operations
    # ------------------------------------------------------------------

    def create_session(self, user_id: str, session_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            row: Dict[str, Any] = {"user_id": user_id}
            if session_data:
                for key in ("title", "overall_score", "shot_count", "duration_seconds", "notes"):
                    if key in session_data:
                        row[key] = session_data[key]
            resp = sb.table("sessions").insert(row).execute()
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("create_session failed", extra={"user_id": user_id})
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("sessions")
                .select("*")
                .eq("id", session_id)
                .maybe_single()
                .execute()
            )
            return resp.data or None
        except Exception:
            logger.exception("get_session failed", extra={"session_id": session_id})
            return None

    def get_user_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_user_sessions failed", extra={"user_id": user_id})
            return []

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("sessions")
                .update(updates)
                .eq("id", session_id)
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("update_session failed", extra={"session_id": session_id})
            return None

    # ------------------------------------------------------------------
    # Video operations
    # ------------------------------------------------------------------

    def create_video(self, user_id: str, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            video_data["user_id"] = user_id
            resp = sb.table("videos").insert(video_data).execute()
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("create_video failed", extra={"user_id": user_id})
            return None

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("videos")
                .select("*")
                .eq("id", video_id)
                .maybe_single()
                .execute()
            )
            return resp.data or None
        except Exception:
            logger.exception("get_video failed", extra={"video_id": video_id})
            return None

    def update_video_status(self, video_id: str, status: str, job_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            updates: Dict[str, Any] = {"processing_status": status}
            if job_id is not None:
                updates["job_id"] = job_id
            resp = (
                sb.table("videos")
                .update(updates)
                .eq("id", video_id)
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("update_video_status failed", extra={"video_id": video_id})
            return None

    def get_user_videos(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("videos")
                .select("id, created_at, fps, file_url, camera_angle, device_info, "
                        "processing_status, job_id, duration_seconds, resolution")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_user_videos failed", extra={"user_id": user_id})
            return []

    # ------------------------------------------------------------------
    # Metrics operations
    # ------------------------------------------------------------------

    def save_metrics(self, video_id: str, metrics_list: List[Dict[str, Any]]) -> List[str]:
        if not metrics_list:
            return []
        try:
            sb = get_service_client()
            rows = [
                {
                    "video_id": video_id,
                    "metric_name": m["metric_name"],
                    "value": float(m["value"]),
                    "confidence": float(m.get("confidence", 0.0)),
                    "unit": m.get("unit"),
                    "phase": m.get("phase"),
                    "frame_idx": m.get("frame_idx"),
                }
                for m in metrics_list
            ]
            resp = sb.table("metrics").insert(rows).execute()
            return [row["id"] for row in (resp.data or [])]
        except Exception:
            logger.exception("save_metrics failed", extra={"video_id": video_id})
            return []

    def get_metrics(self, video_id: str) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("metrics")
                .select("id, metric_name, value, unit, confidence, phase, frame_idx, created_at")
                .eq("video_id", video_id)
                .order("created_at", desc=False)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_metrics failed", extra={"video_id": video_id})
            return []

    # ------------------------------------------------------------------
    # Feedback operations
    # ------------------------------------------------------------------

    def save_feedback(self, items: List[Dict[str, Any]]) -> List[str]:
        if not items:
            return []
        try:
            sb = get_service_client()
            resp = sb.table("feedback").insert(items).execute()
            return [row["id"] for row in (resp.data or [])]
        except Exception:
            logger.exception("save_feedback failed")
            return []

    def get_feedback_for_video(self, video_id: str) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            metric_ids_resp = (
                sb.table("metrics")
                .select("id")
                .eq("video_id", video_id)
                .execute()
            )
            metric_ids = [m["id"] for m in (metric_ids_resp.data or [])]
            if not metric_ids:
                return []
            resp = (
                sb.table("feedback")
                .select("id, metric_id, message, severity, created_at")
                .in_("metric_id", metric_ids)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_feedback_for_video failed", extra={"video_id": video_id})
            return []

    # ------------------------------------------------------------------
    # Analysis summary operations (critical for Coach J)
    # ------------------------------------------------------------------

    def save_analysis_summary(
        self, session_id: str, user_id: str, summary_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            row = {
                "session_id": session_id,
                "user_id": user_id,
                **summary_data,
            }
            resp = (
                sb.table("analysis_summaries")
                .upsert(row, on_conflict="session_id")
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("save_analysis_summary failed", extra={"session_id": session_id})
            return None

    def get_recent_summaries(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("analysis_summaries")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_recent_summaries failed", extra={"user_id": user_id})
            return []

    # ------------------------------------------------------------------
    # Chat history operations
    # ------------------------------------------------------------------

    def save_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            row: Dict[str, Any] = {
                "user_id": user_id,
                "role": role,
                "content": content,
            }
            if session_id:
                row["session_id"] = session_id
            if metadata:
                row["model_used"] = metadata.get("model")
                row["token_count"] = metadata.get("tokens")
                row["response_time_ms"] = metadata.get("response_time_ms")
            resp = sb.table("chat_history").insert(row).execute()
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("save_chat_message failed", extra={"user_id": user_id, "role": role})
            return None

    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("chat_history")
                .select("id, role, content, session_id, model_used, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_chat_history failed", extra={"user_id": user_id})
            return []

    def clear_chat_history(self, user_id: str) -> bool:
        try:
            sb = get_service_client()
            sb.table("chat_history").delete().eq("user_id", user_id).execute()
            return True
        except Exception:
            logger.exception("clear_chat_history failed", extra={"user_id": user_id})
            return False

    # ------------------------------------------------------------------
    # Drill + Workout operations
    # ------------------------------------------------------------------

    def save_drill_completion(self, user_id: str, drill_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            row = {"user_id": user_id, **drill_data}
            resp = sb.table("drill_completions").insert(row).execute()
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("save_drill_completion failed", extra={"user_id": user_id})
            return None

    def get_drill_completions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("drill_completions")
                .select("*")
                .eq("user_id", user_id)
                .order("completed_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_drill_completions failed", extra={"user_id": user_id})
            return []

    def upsert_workout_progress(
        self, user_id: str, workout_id: str, progress_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            row = {"user_id": user_id, "workout_id": workout_id, **progress_data}
            resp = (
                sb.table("workout_progress")
                .upsert(row, on_conflict="user_id,workout_id")
                .execute()
            )
            return resp.data[0] if resp.data else None
        except Exception:
            logger.exception("upsert_workout_progress failed", extra={"user_id": user_id})
            return None

    def get_workout_progress(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("workout_progress")
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_workout_progress failed", extra={"user_id": user_id})
            return []

    # ------------------------------------------------------------------
    # Streak operations
    # ------------------------------------------------------------------

    def update_streak(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            sb.rpc("update_user_streak", {"p_user_id": user_id}).execute()
            return self.get_streak(user_id)
        except Exception:
            logger.exception("update_streak failed", extra={"user_id": user_id})
            return None

    def get_streak(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("user_streaks")
                .select("current_streak, longest_streak, last_activity_date, updated_at")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            return resp.data or None
        except Exception:
            logger.exception("get_streak failed", extra={"user_id": user_id})
            return None

    # ------------------------------------------------------------------
    # Session videos (join table — kept from existing schema)
    # ------------------------------------------------------------------

    def add_video_to_session(self, session_id: str, video_id: str) -> bool:
        try:
            sb = get_service_client()
            sb.table("session_videos").insert({
                "session_id": session_id,
                "video_id": video_id,
            }).execute()
            return True
        except Exception:
            logger.exception("add_video_to_session failed",
                             extra={"session_id": session_id, "video_id": video_id})
            return False

    def get_session_videos(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            sb = get_service_client()
            resp = (
                sb.table("session_videos")
                .select("video_id, videos(*)")
                .eq("session_id", session_id)
                .execute()
            )
            return resp.data or []
        except Exception:
            logger.exception("get_session_videos failed", extra={"session_id": session_id})
            return []

    def get_user_analysis_history(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return sessions with analysis_summaries and per-video metrics (MVP scores).

        Ordered by analysis summary ``created_at`` descending (most recent first).

        Prior implementation was O(N) round-trips: one ``get_session`` +
        ``get_session_videos`` + ``get_metrics`` per summary. On a user with 100
        sessions that produced ~300 Supabase calls and explained the 5-10s
        "Home"/"Progress" spinners. This version batches everything into four
        queries regardless of N.
        """
        if limit <= 0:
            return []
        try:
            sb = get_service_client()
            # 1. Summaries (latest first).
            summ_resp = (
                sb.table("analysis_summaries")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            rows = summ_resp.data or []
            session_ids = [str(r["session_id"]) for r in rows if r.get("session_id")]
            if not session_ids:
                return []

            # 2. Sessions in one round-trip.
            sess_resp = (
                sb.table("sessions")
                .select("id, title, timestamp, shot_count, overall_score")
                .in_("id", session_ids)
                .execute()
            )
            sessions_by_id: Dict[str, Dict[str, Any]] = {
                str(s["id"]): s for s in (sess_resp.data or [])
            }

            # 3. session -> video_id mapping in one round-trip.
            sv_resp = (
                sb.table("session_videos")
                .select("session_id, video_id")
                .in_("session_id", session_ids)
                .execute()
            )
            session_to_video: Dict[str, str] = {}
            for sv in sv_resp.data or []:
                sid = str(sv.get("session_id")) if sv.get("session_id") else None
                vid = str(sv.get("video_id")) if sv.get("video_id") else None
                if sid and vid and sid not in session_to_video:
                    session_to_video[sid] = vid
            video_ids = list(session_to_video.values())

            # 4. All metrics for those videos in one round-trip.
            metrics_by_video: Dict[str, List[Dict[str, Any]]] = {}
            if video_ids:
                m_resp = (
                    sb.table("metrics")
                    .select("id, video_id, metric_name, value, unit, confidence, phase, frame_idx, created_at")
                    .in_("video_id", video_ids)
                    .order("created_at", desc=False)
                    .execute()
                )
                for m in m_resp.data or []:
                    vid = str(m.get("video_id")) if m.get("video_id") else None
                    if not vid:
                        continue
                    metrics_by_video.setdefault(vid, []).append(m)

            out: List[Dict[str, Any]] = []
            for summ in rows:
                session_id = summ.get("session_id")
                if not session_id:
                    continue
                sid = str(session_id)
                session = sessions_by_id.get(sid)
                video_id = session_to_video.get(sid)
                metrics = metrics_by_video.get(video_id, []) if video_id else []
                ts = (
                    (session or {}).get("timestamp")
                    or summ.get("created_at")
                    or ""
                )
                title = (session or {}).get("title")
                shot_count = (session or {}).get("shot_count") or summ.get("shot_count") or 1
                overall = summ.get("overall_score")
                if overall is None and session:
                    overall = session.get("overall_score")
                out.append({
                    "session_id": sid,
                    "video_id": video_id,
                    "timestamp": ts,
                    "title": title,
                    "date": str(ts)[:10] if ts else "",
                    "shot_count": int(shot_count) if shot_count is not None else 1,
                    "average_score": float(overall) if overall is not None else None,
                    "overall_score": float(overall) if overall is not None else None,
                    "score_tier": summ.get("score_tier"),
                    "top_strengths": summ.get("top_strengths") or [],
                    "top_improvements": summ.get("top_improvements") or [],
                    "metrics": metrics,
                })
            return out
        except Exception:
            logger.exception("get_user_analysis_history failed", extra={"user_id": user_id})
            return []

    def delete_all_data_for_user(self, user_id: str) -> bool:
        """Remove user-owned rows in public schema (service role). Order respects FKs."""
        try:
            sb = get_service_client()
            sb.table("chat_history").delete().eq("user_id", user_id).execute()

            vresp = (
                sb.table("videos")
                .select("id")
                .eq("user_id", user_id)
                .execute()
            )
            video_ids = [r["id"] for r in (vresp.data or [])]
            if video_ids:
                mresp = (
                    sb.table("metrics")
                    .select("id")
                    .in_("video_id", video_ids)
                    .execute()
                )
                metric_ids = [r["id"] for r in (mresp.data or [])]
                if metric_ids:
                    sb.table("feedback").delete().in_("metric_id", metric_ids).execute()
                sb.table("metrics").delete().in_("video_id", video_ids).execute()

            sresp = (
                sb.table("sessions")
                .select("id")
                .eq("user_id", user_id)
                .execute()
            )
            session_ids = [r["id"] for r in (sresp.data or [])]
            if session_ids:
                sb.table("session_videos").delete().in_("session_id", session_ids).execute()

            sb.table("analysis_summaries").delete().eq("user_id", user_id).execute()
            sb.table("videos").delete().eq("user_id", user_id).execute()
            sb.table("sessions").delete().eq("user_id", user_id).execute()
            sb.table("drill_completions").delete().eq("user_id", user_id).execute()
            sb.table("workout_progress").delete().eq("user_id", user_id).execute()
            sb.table("user_streaks").delete().eq("user_id", user_id).execute()
            sb.table("user_profiles").delete().eq("user_id", user_id).execute()
            sb.table("users").delete().eq("id", user_id).execute()
            logger.info("delete_all_data_for_user completed", extra={"user_id": user_id})
            return True
        except Exception:
            logger.exception("delete_all_data_for_user failed", extra={"user_id": user_id})
            return False


# Module-level singleton
db = SupabaseDB()


# Backward-compatible function aliases so existing imports keep working
def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    return db.get_user(user_id)


def record_video(user_id: str, file_url: str, camera_angle: Optional[str] = None,
                 fps: Optional[int] = None, device_info: Optional[str] = None) -> str:
    data: Dict[str, Any] = {"file_url": file_url}
    if camera_angle:
        data["camera_angle"] = camera_angle
    if fps is not None:
        data["fps"] = fps
    if device_info:
        data["device_info"] = device_info
    result = db.create_video(user_id, data)
    return result["id"] if result else ""


def record_metrics(video_id: str, metrics: List[Dict[str, Any]]) -> List[str]:
    return db.save_metrics(video_id, metrics)


def record_feedback(items: List[Dict[str, Any]]) -> List[str]:
    return db.save_feedback(items)


def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    return db.get_user_videos(user_id)


def get_video_metrics(video_id: str) -> List[Dict[str, Any]]:
    return db.get_metrics(video_id)


def get_video_feedback(video_id: str) -> List[Dict[str, Any]]:
    return db.get_feedback_for_video(video_id)


def create_session(user_id: str, title: Optional[str] = None, **_kwargs: Any) -> str:
    data: Dict[str, Any] = {}
    if title:
        data["title"] = title
    result = db.create_session(user_id, data)
    return result["id"] if result else ""


def add_video_to_session(session_id: str, video_id: str) -> bool:
    return db.add_video_to_session(session_id, video_id)


def get_session_videos(session_id: str) -> List[Dict[str, Any]]:
    return db.get_session_videos(session_id)
