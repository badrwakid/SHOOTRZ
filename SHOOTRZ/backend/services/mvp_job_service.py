from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import psutil
from fastapi import BackgroundTasks, HTTPException, UploadFile

from ..contracts.mvp import MVPAnalyzeQueuedResponse, MVPResultResponse
from ..inference.phase_detector import PhaseDetector
from ..inference.pose_2d import BASKETBALL_KEYPOINTS
from ..mvp.core.pipeline import MVPPipeline
from ..services.job_store import DurableJobStore
from ..services.llm import llm_service
from ..storage.db import db
from ..utils.id_gen import generate_job_id
from ..utils.video_annotator import annotate_video


logger = logging.getLogger(__name__)
CONTRACT_VERSION = "mvp-v1.1"


def clean_nan_for_json(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, np.ndarray):
        return [clean_nan_for_json(item) for item in obj.tolist()]
    if isinstance(obj, float):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: clean_nan_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_nan_for_json(item) for item in obj]
    return obj


def _timestamp_for_frame(angles_df: pd.DataFrame, frame_id: Optional[int]) -> Optional[float]:
    if frame_id is None or angles_df.empty:
        return None
    m = angles_df[angles_df["frame_id"] == frame_id]
    if len(m):
        val = m.iloc[0].get("timestamp")
        return None if pd.isna(val) else float(val)
    nearest_idx = (angles_df["frame_id"] - int(frame_id)).abs().idxmin()
    val = angles_df.loc[nearest_idx].get("timestamp")
    return None if pd.isna(val) else float(val)


def _build_events_payload(shot_window: Dict[str, Any], angles_df: pd.DataFrame) -> Dict[str, Any]:
    events = shot_window.get("events") or {}
    out: Dict[str, Any] = {}
    legacy_map = {
        "start": "start_frame",
        "crouch": "crouch_frame",
        "release": "release_frame",
        "end": "end_frame",
    }
    for event_name, legacy_key in legacy_map.items():
        payload = dict(events.get(event_name) or {})
        frame_val = payload.get("frame", shot_window.get(legacy_key))
        frame_val = int(frame_val) if frame_val is not None else None
        out[event_name] = {
            "frame": frame_val,
            "timestamp": _timestamp_for_frame(angles_df, frame_val),
            "status": payload.get("status", "estimated"),
            "confidence": float(payload.get("confidence", 0.0)),
            "reason_codes": list(payload.get("reason_codes", [])),
            "alternatives": payload.get("alternatives", []),
        }
    return out


class MVPJobService:
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.outputs_dir = self.backend_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.job_store = DurableJobStore(self.outputs_dir / "jobs.sqlite3", retention_hours=72)
        self.artifact_retention_days = 7

    def queue_job(
        self,
        background_tasks: BackgroundTasks,
        upload: UploadFile,
        shooting_side: str = "auto",
    ) -> MVPAnalyzeQueuedResponse:
        job_id = generate_job_id()
        suffix = Path(upload.filename).suffix if upload.filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(upload.file, tmp_file)
            video_path = tmp_file.name

        self.job_store.cleanup_expired()
        self.cleanup_old_outputs()
        self.job_store.upsert(job_id, {"status": "queued"})
        background_tasks.add_task(self._process_video_job, job_id, video_path, shooting_side)
        logger.info("Queued MVP analysis job", extra={"job_id": job_id})
        return MVPAnalyzeQueuedResponse(job_id=job_id, status="queued")

    def get_result(self, job_id: str) -> MVPResultResponse:
        payload = self.job_store.get(job_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return MVPResultResponse(**payload)

    def get_artifact_path(self, run_id: str, filename: str) -> Path:
        run_dir = (self.outputs_dir / run_id).resolve()
        artifact_path = (run_dir / filename).resolve()

        if not str(artifact_path).startswith(str(run_dir)):
            raise HTTPException(status_code=400, detail="Invalid artifact path")
        if not artifact_path.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return artifact_path

    def _set_status(self, job_id: str, payload: Dict[str, Any]) -> None:
        self.job_store.upsert(job_id, clean_nan_for_json(payload))

    def _process_video_job(self, job_id: str, video_path: str, shooting_side: str = "auto") -> None:
        self._set_status(job_id, {"status": "processing"})
        try:
            pipeline = MVPPipeline()
            proc = psutil.Process(os.getpid())
            mem_before_mb = proc.memory_info().rss / 1024 ** 2
            t_total_start = time.perf_counter()
            result = pipeline.process_video(
                video_path,
                shooting_side,
                peak_memory_sampler=lambda: proc.memory_info().rss / 1024 ** 2,
            )
            elapsed_s = time.perf_counter() - t_total_start
            mem_after_mb = proc.memory_info().rss / 1024 ** 2
            peak_mem_mb = max(
                mem_before_mb,
                mem_after_mb,
                float(result.get("peak_memory_mb") or 0.0),
            )
            logger.info("Pipeline completed", extra={"job_id": job_id, "run_id": result.get("run_id")})

            angles_csv = Path(result["output_dir"]) / "angles.csv"
            if not angles_csv.exists():
                raise FileNotFoundError(f"Angles CSV not found: {angles_csv}")

            angles_df = pd.read_csv(angles_csv)
            angles_data = {
                "frames": angles_df["frame_id"].fillna(0).astype(int).tolist(),
                "timestamps": angles_df["timestamp"].fillna(0.0).tolist(),
                "elbow": [None if pd.isna(x) else float(x) for x in angles_df["elbow_angle"]],
                "knee": [None if pd.isna(x) else float(x) for x in angles_df["knee_angle"]],
                "wrist": [None if pd.isna(x) else float(x) for x in angles_df["wrist_angle"]],
            }

            overall_score = result.get("overall_score", 0)
            if pd.isna(overall_score) or np.isnan(overall_score) or overall_score < 0:
                overall_score = 0
            elif overall_score > 100:
                overall_score = 100

            metrics = result.get("metrics", [])
            if not isinstance(metrics, list):
                metrics = []

            sw_payload = dict(result.get("shot_window") or {})
            ev_diag = sw_payload.pop("diagnostics", None)
            job_diag = dict(result.get("diagnostics") or {})
            if ev_diag is not None:
                job_diag["events"] = ev_diag

            job_result: Dict[str, Any] = {
                "status": "completed",
                "contract_version": CONTRACT_VERSION,
                "run_id": result["run_id"],
                "metrics": metrics,
                "overall_score": int(overall_score),
                "feedback_summary": result.get("feedback_summary", "Analysis completed successfully"),
                "feedback_bullets": result.get("feedback_bullets") or [],
                "score_components": result.get("score_components") or [],
                "shot_window": sw_payload,
                "events": _build_events_payload(result.get("shot_window") or {}, angles_df),
                "shooting_side": result.get("shooting_side", "right"),
                "angles_data": angles_data,
                "artifacts": {
                    "overlay_video": f"/mvp/artifacts/{result['run_id']}/overlay.mp4",
                    "angles_csv": f"/mvp/artifacts/{result['run_id']}/angles.csv",
                    "report_json": f"/mvp/artifacts/{result['run_id']}/report.json",
                    "event_candidates": f"/mvp/artifacts/{result['run_id']}/event_candidates.json",
                    "event_confidence": f"/mvp/artifacts/{result['run_id']}/event_confidence.json",
                    "feature_table": f"/mvp/artifacts/{result['run_id']}/feature_table.csv",
                    "signals_smoothed": f"/mvp/artifacts/{result['run_id']}/signals_smoothed.csv",
                    "warnings": f"/mvp/artifacts/{result['run_id']}/warnings.json",
                },
                "key_frame_images": {},
                "quality_warnings": result.get("quality_warnings", []),
                "diagnostics": job_diag,
                "processing_time_seconds": round(elapsed_s, 3),
                "phase_timings_seconds": result.get("phase_timings_seconds", {}),
                "peak_memory_mb": round(peak_mem_mb, 1),
                "pose_overall_confidence": result.get("pose_overall_confidence"),
            }

            key_frame_images = result.get("key_frame_images") or {}
            if isinstance(key_frame_images, dict):
                for event_name, name in key_frame_images.items():
                    if isinstance(name, str) and name:
                        job_result["key_frame_images"][event_name] = (
                            f"/mvp/artifacts/{result['run_id']}/{name}"
                        )

            self._enrich_with_gemini(job_result)
            self._build_overlay_artifact(job_id, result, video_path, job_result)
            self._save_to_supabase(job_id, job_result)
            run_meta_path = Path(result["output_dir"]) / "run_metadata.json"
            if run_meta_path.exists():
                with open(run_meta_path, "r", encoding="utf-8") as rf:
                    run_meta = json.load(rf)
            else:
                run_meta = {}
            run_meta.update(
                {
                    "job_id": job_id,
                    "processing_time_seconds": round(elapsed_s, 3),
                    "phase_timings_seconds": result.get("phase_timings_seconds", {}),
                    "memory_before_mb": round(mem_before_mb, 1),
                    "memory_after_mb": round(mem_after_mb, 1),
                    "peak_memory_mb": round(peak_mem_mb, 1),
                    "pose_overall_confidence": result.get("pose_overall_confidence"),
                }
            )
            with open(run_meta_path, "w", encoding="utf-8") as wf:
                json.dump(clean_nan_for_json(run_meta), wf, indent=2)
            self._set_status(job_id, job_result)
            logger.info("Job completed successfully", extra={"job_id": job_id, "status": "completed"})
        except Exception as exc:
            logger.exception("Job failed", extra={"job_id": job_id, "error_type": type(exc).__name__})
            error_message = str(exc)
            if "FileNotFoundError" in type(exc).__name__:
                error_message = "Video file processing failed. Please try recording a new video."
            elif "MediaPipeError" in str(exc) or "pose" in str(exc).lower():
                error_message = "Could not detect pose in video. Please ensure the shooter is clearly visible."
            elif "angles" in str(exc).lower() or "joint" in str(exc).lower():
                error_message = "Could not compute shooting angles. Please ensure full body is visible in frame."

            self._set_status(
                job_id,
                {
                    "status": "failed",
                    "error": error_message,
                    "error_detail": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
        finally:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                logger.warning("Failed to remove temporary upload", extra={"job_id": job_id})

    def _enrich_with_gemini(self, job_result: Dict[str, Any]) -> None:
        """Replace rule-based feedback text with Gemini-generated content.

        Falls back silently to the existing rule-based values already in
        ``job_result`` — so this is always safe to call.
        """
        try:
            overall = job_result.get("overall_score", 0)
            tier = "poor"
            if overall >= 90:
                tier = "elite"
            elif overall >= 75:
                tier = "great"
            elif overall >= 60:
                tier = "good"
            elif overall >= 40:
                tier = "fair"

            fb = llm_service.get_shot_feedback(
                metrics=job_result.get("metrics", []),
                score_components=job_result.get("score_components", []),
                overall_score=overall,
                score_tier=tier,
                feedback_summary=job_result.get("feedback_summary", ""),
                feedback_bullets=job_result.get("feedback_bullets", []),
            )

            job_result["feedback_summary"] = fb.overall_explanation
            job_result["feedback_bullets"] = fb.feedback_bullets

            for m in job_result.get("metrics", []):
                for me in fb.metric_explanations:
                    if me.metric_name == m.get("name"):
                        m["explanation"] = me.explanation
                        break

            job_result["gemini_strengths"] = fb.strengths
            job_result["gemini_improvements"] = fb.improvements
            job_result["gemini_enriched"] = True
            logger.info("Shot feedback enriched with Gemini")
        except Exception:
            logger.warning("Gemini enrichment skipped, using rule-based feedback", exc_info=True)
            job_result["gemini_enriched"] = False

    def _save_to_supabase(self, job_id: str, job_result: Dict[str, Any]) -> None:
        """Persist completed analysis to Supabase for Coach J context and history.

        This is best-effort — failures here should not break the pipeline.
        The user_id is not available in the current unauthenticated MVP flow,
        so this will be called with user_id when triggered from an authenticated
        endpoint. For now, it stores session-level data keyed by job_id.
        """
        try:
            run_id = job_result.get("run_id", job_id)
            overall = job_result.get("overall_score", 0)
            metrics = job_result.get("metrics", [])

            def _extract_metric(name_contains: str) -> Dict[str, Any]:
                for m in metrics:
                    mname = (m.get("name") or "").lower()
                    if name_contains in mname:
                        return m
                return {}

            elbow = _extract_metric("elbow")
            knee = _extract_metric("knee")
            release = _extract_metric("release")
            follow = _extract_metric("follow")
            balance = _extract_metric("balance")

            score_components = job_result.get("score_components", [])
            bullets = job_result.get("feedback_bullets", [])

            if job_result.get("gemini_enriched"):
                strengths = job_result.get("gemini_strengths", [])[:3]
                improvements = job_result.get("gemini_improvements", [])[:3]
            else:
                strengths = [b for b in bullets if any(
                    w in b.lower() for w in ("good", "great", "strong", "excellent", "nice")
                )][:3]
                improvements = [b for b in bullets if any(
                    w in b.lower() for w in ("improve", "work on", "try", "focus", "need")
                )][:3]
            if not improvements:
                improvements = bullets[:3]

            tier = "poor"
            if overall >= 90:
                tier = "elite"
            elif overall >= 75:
                tier = "great"
            elif overall >= 60:
                tier = "good"
            elif overall >= 40:
                tier = "fair"

            session_summary = None
            try:
                session_data = {
                    "overall_score": overall,
                    "score_tier": tier,
                    "strengths": strengths,
                    "improvements": improvements,
                    "metrics": [
                        {"name": m.get("name"), "value": m.get("value"), "verdict": m.get("verdict")}
                        for m in metrics
                    ],
                }
                session_summary = llm_service.get_session_summary(session_data=session_data)
            except Exception:
                logger.warning("Gemini session summary failed", exc_info=True)

            summary_strengths = strengths
            summary_improvements = improvements
            if session_summary:
                if session_summary.key_takeaway:
                    summary_improvements = [session_summary.key_takeaway] + improvements[:2]

            summary_dict = {
                "overall_score": overall,
                "shot_count": 1,
                "elbow_angle_score": elbow.get("value"),
                "knee_bend_score": knee.get("value"),
                "release_angle_score": release.get("value"),
                "follow_through_score": follow.get("value"),
                "balance_score": balance.get("value"),
                "top_strengths": summary_strengths,
                "top_improvements": summary_improvements,
                "score_tier": tier,
            }
            job_result["supabase_summary"] = summary_dict
            logger.info("Analysis summary prepared for Supabase",
                        extra={"job_id": job_id, "tier": tier, "score": overall})
        except Exception:
            logger.exception("Failed to prepare Supabase summary", extra={"job_id": job_id})

    def save_result_for_user(
        self, job_id: str, user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Persist completed job results to Supabase for the authenticated user.

        Idempotent: if this job was already saved for this user, returns the
        stored session/video ids without inserting duplicate rows.
        """
        try:
            payload = self.job_store.get(job_id)
            if not payload or payload.get("status") != "completed":
                logger.warning(
                    "save_result_for_user: job not completed",
                    extra={"job_id": job_id, "status": payload.get("status") if payload else None},
                )
                return None

            prev = payload.get("supabase_persisted")
            if isinstance(prev, dict) and prev.get("user_id") == user_id:
                logger.info(
                    "save_result_for_user: already persisted",
                    extra={"job_id": job_id, "user_id": user_id},
                )
                return {
                    "success": True,
                    "session_id": prev.get("session_id"),
                    "video_id": prev.get("video_id"),
                    "already_persisted": True,
                }

            session = db.create_session(user_id, {
                "title": f"Analysis {job_id[:8]}",
                "overall_score": payload.get("overall_score", 0),
                "shot_count": 1,
            })
            if not session:
                logger.warning("Failed to create session", extra={"job_id": job_id})
                return None

            session_id = session["id"]

            video = db.create_video(user_id, {
                "file_url": f"/mvp/artifacts/{payload.get('run_id', job_id)}/overlay.mp4",
                "processing_status": "completed",
                "job_id": job_id,
            })
            video_id = video["id"] if video else None

            if video_id:
                db.add_video_to_session(session_id, video_id)

                raw_metrics = payload.get("metrics", [])
                if raw_metrics:
                    metric_rows = [
                        {
                            "metric_name": m.get("name", ""),
                            "value": float(m.get("value", 0)),
                            "confidence": float(m.get("confidence", 0)),
                            "unit": m.get("unit", ""),
                        }
                        for m in raw_metrics
                    ]
                    db.save_metrics(video_id, metric_rows)

            summary = payload.get("supabase_summary")
            if summary:
                db.save_analysis_summary(session_id, user_id, summary)

            db.update_streak(user_id)

            out = {
                "success": True,
                "session_id": session_id,
                "video_id": video_id,
                "already_persisted": False,
            }
            payload["supabase_persisted"] = {
                "user_id": user_id,
                "session_id": session_id,
                "video_id": video_id,
            }
            self._set_status(job_id, payload)
            logger.info(
                "Results saved to Supabase",
                extra={"job_id": job_id, "user_id": user_id, "session_id": session_id},
            )
            return out
        except Exception:
            logger.exception("Failed to save results to Supabase", extra={"job_id": job_id})
            return None

    def cleanup_old_outputs(self) -> None:
        cutoff = time.time() - (self.artifact_retention_days * 86400)
        for item in self.outputs_dir.iterdir():
            if not item.is_dir():
                continue
            try:
                if item.stat().st_mtime < cutoff:
                    shutil.rmtree(item, ignore_errors=True)
            except Exception:
                logger.warning("Failed to cleanup output directory", extra={"path": str(item)})

    def _build_overlay_artifact(
        self,
        job_id: str,
        result: Dict[str, Any],
        video_path: str,
        job_result: Dict[str, Any],
    ) -> None:
        try:
            pose_json_path = Path(result["output_dir"]) / "pose_keypoints.json"
            shot_window_path = Path(result["output_dir"]) / "shot_window.json"
            overlay_path = Path(result["output_dir"]) / "overlay.mp4"
            input_video_path = Path(result["output_dir"]) / "input_video.mp4"
            overlay_video_path = str(input_video_path) if input_video_path.exists() else str(video_path)

            with open(pose_json_path, "r", encoding="utf-8") as handle:
                pose_json = json.load(handle)

            pose_frames = pose_json.get("frames", [])
            keypoint_count = max(BASKETBALL_KEYPOINTS.values()) + 1
            pose_results = []
            for frame in pose_frames:
                frame_idx = frame.get("frame_idx", 0)
                joints = frame.get("joints", {})
                landmarks = np.zeros((keypoint_count, 3), dtype=float)
                confidence = np.zeros((keypoint_count,), dtype=float)
                for joint_name, joint_data in joints.items():
                    if joint_name not in BASKETBALL_KEYPOINTS:
                        continue
                    idx = BASKETBALL_KEYPOINTS[joint_name]
                    landmarks[idx, 0] = joint_data.get("x_norm", 0.0)
                    landmarks[idx, 1] = joint_data.get("y_norm", 0.0)
                    landmarks[idx, 2] = joint_data.get("z_norm", 0.0)
                    confidence[idx] = joint_data.get("confidence", 0.0)
                pose_results.append(
                    {"frame_idx": frame_idx, "landmarks": landmarks, "confidence": confidence}
                )

            phases = []
            try:
                if not pose_results:
                    raise ValueError("pose_results is empty - cannot detect phases")
                fps = pose_json.get("video_metadata", {}).get("fps", 30.0)
                # BUG FIX: Pass shooting_side to PhaseDetector for correct landmark selection
                phase_detector = PhaseDetector(fps=fps, shooting_side=result.get("shooting_side", "right"))
                phases = phase_detector.detect_phases(pose_results)
                if phases:
                    converted = []
                    for phase in phases:
                        start_idx = int(phase.get("start_frame", 0))
                        end_idx = int(phase.get("end_frame", start_idx))
                        peak_idx = phase.get("peak_frame")
                        start_idx = max(0, min(start_idx, len(pose_results) - 1))
                        end_idx = max(0, min(end_idx, len(pose_results) - 1))
                        mapped = dict(phase)
                        mapped["start_frame"] = int(pose_results[start_idx]["frame_idx"])
                        mapped["end_frame"] = int(pose_results[end_idx]["frame_idx"])
                        if isinstance(peak_idx, int) and len(pose_results) > 0:
                            peak_idx = max(0, min(peak_idx, len(pose_results) - 1))
                            mapped["peak_frame"] = int(pose_results[peak_idx]["frame_idx"])
                        converted.append(mapped)
                    phases = converted
                    job_result["phase_detector_version"] = "motion_based_v2"
                    job_result["phase_detected_at"] = time.time()
            except Exception:
                logger.warning("Phase detection failed, using fallback", exc_info=True)
                if shot_window_path.exists():
                    with open(shot_window_path, "r", encoding="utf-8") as handle:
                        sw = json.load(handle)
                    phases = [
                        {
                            "phase": "stance",
                            "start_frame": sw.get("start_frame", 0),
                            "end_frame": sw.get("crouch_frame", 0),
                        },
                        {
                            "phase": "crouch",
                            "start_frame": sw.get("crouch_frame", 0),
                            "end_frame": sw.get("release_frame", 0),
                        },
                        {
                            "phase": "release",
                            "start_frame": sw.get("release_frame", 0),
                            "end_frame": sw.get("end_frame", sw.get("release_frame", 0)),
                        },
                    ]
                job_result["phase_detector_version"] = "fallback"
                job_result["phase_detected_at"] = time.time()

            annotate_video(
                video_path=overlay_video_path,
                pose_results=pose_results,
                phases=phases,
                output_path=str(overlay_path),
                fps=pose_json.get("video_metadata", {}).get("fps", 30.0),
            )
            if not overlay_path.exists():
                raise FileNotFoundError(f"Overlay was not created at: {overlay_path}")
            job_result["artifacts"]["overlay_video"] = f"/mvp/artifacts/{result['run_id']}/overlay.mp4"
            logger.info(
                "Overlay generation complete",
                extra={"job_id": job_id, "run_id": result["run_id"], "overlay_path": str(overlay_path)},
            )
        except Exception as overlay_error:
            logger.exception(
                "Overlay generation failed",
                extra={"job_id": job_id, "run_id": result["run_id"], "error": str(overlay_error)},
            )
            job_result["artifacts"]["overlay_video"] = None

