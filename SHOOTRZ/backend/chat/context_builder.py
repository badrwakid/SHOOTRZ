from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..storage import db


def _safe_iso(dt_str: Optional[str]) -> Optional[str]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).isoformat()
    except Exception:
        return dt_str


def _summarize_metrics(metrics: List[Dict[str, Any]], max_items: int = 20) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for m in metrics[:max_items]:
        items.append(
            {
                "metric_name": m.get("metric_name"),
                "value": m.get("value"),
                "unit": m.get("unit"),
                "confidence": m.get("confidence"),
                "phase": m.get("phase"),
                "frame_idx": m.get("frame_idx"),
            }
        )
    return items


def _aggregate_recent_scores(video_metrics: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    # Very simple aggregation: average of metric values across all metrics we saw.
    values: List[float] = []
    for metrics in video_metrics:
        for m in metrics:
            v = m.get("value")
            if isinstance(v, (int, float)):
                values.append(float(v))
    if not values:
        return {"average_metric_value": None, "count": 0}
    avg = sum(values) / len(values)
    return {"average_metric_value": round(avg, 2), "count": len(values)}


def _read_recent_artifact_summaries(run_id: str, max_bytes: int = 50_000) -> Dict[str, Any]:
    """
    Best-effort artifact summarizer for locally stored MVP outputs.
    NOTE: This only works if the server has the outputs directory and the run_id exists.
    """
    backend_dir = Path(__file__).parent.parent
    base = backend_dir / "outputs" / run_id
    if not base.exists():
        return {"available": False}

    def _read_json(name: str) -> Optional[Dict[str, Any]]:
        p = base / name
        if not p.exists():
            return None
        raw = p.read_text(encoding="utf-8", errors="ignore")
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        try:
            import json

            return json.loads(raw)
        except Exception:
            return None

    return {
        "available": True,
        "shot_window": _read_json("shot_window.json"),
        "report": _read_json("report.json"),
        "confidence_summary": _read_json("confidence_summary.json"),
        "video_metadata": _read_json("video_metadata.json"),
    }


@dataclass(frozen=True)
class ContextBuildOptions:
    include_raw_artifacts: bool = False
    max_videos: int = 8
    max_metrics_per_video: int = 25


def build_user_context(
    *,
    user_id: str,
    user_local_context: Optional[Dict[str, Any]],
    options: ContextBuildOptions,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Build a context object for the LLM using BOTH:
    - server-side Supabase data (trusted, scoped by user_id)
    - client-side local context (goals, preferences, drill completions, cached analyses)
    """
    profile = db.get_user_profile(user_id)
    videos = db.get_user_history(user_id)[: options.max_videos]

    video_summaries: List[Dict[str, Any]] = []
    all_video_metrics: List[List[Dict[str, Any]]] = []

    for v in videos:
        vid = v.get("id")
        metrics = db.get_video_metrics(vid) if vid else []
        all_video_metrics.append(metrics)
        video_summaries.append(
            {
                "video_id": vid,
                "created_at": _safe_iso(v.get("created_at")),
                "angle": v.get("angle") or v.get("camera_angle"),
                "fps": v.get("fps"),
                "device": v.get("device"),
                "file_url": v.get("file_url"),
                "metrics": _summarize_metrics(metrics, max_items=options.max_metrics_per_video),
            }
        )

    aggregates = _aggregate_recent_scores(all_video_metrics)

    artifacts_summary = None
    artifacts_available = False
    artifacts_reason = None
    
    if options.include_raw_artifacts:
        # We don't have a stable mapping of user->run_id today.
        # If the client provides a run_id in local context, we can summarize it best-effort.
        run_id = None
        if isinstance(user_local_context, dict):
            run_id = user_local_context.get("latest_run_id") or user_local_context.get("run_id")
        if isinstance(run_id, str) and run_id.strip():
            artifacts_summary = _read_recent_artifact_summaries(run_id.strip())
            artifacts_available = artifacts_summary.get("available", False)
            if not artifacts_available:
                artifacts_reason = f"Run outputs not found for run_id={run_id[:16]}"
        else:
            artifacts_summary = {"available": False, "reason": "No run_id provided by client"}
            artifacts_reason = "No run_id provided by client"

    context: Dict[str, Any] = {
        "user_profile": profile,
        "server_history": {
            "recent_videos": video_summaries,
            "aggregates": aggregates,
        },
        "client_local": user_local_context or {},
        "artifacts_summary": artifacts_summary,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    context_used = {
        "profile": bool(profile),
        "recent_videos_count": len(video_summaries),
        "include_raw_artifacts": options.include_raw_artifacts,
        "has_client_local_context": bool(user_local_context),
        "artifacts_requested": options.include_raw_artifacts,
        "artifacts_available": artifacts_available,
        "artifacts_reason": artifacts_reason,
    }
    return context, context_used



