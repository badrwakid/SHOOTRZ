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
from fastapi import BackgroundTasks, HTTPException, UploadFile

from ..contracts.mvp import MVPAnalyzeQueuedResponse, MVPResultResponse
from ..inference.phase_detector import PhaseDetector
from ..inference.pose_2d import BASKETBALL_KEYPOINTS
from ..mvp.core.pipeline import MVPPipeline
from ..services.job_store import DurableJobStore
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
            result = pipeline.process_video(video_path, shooting_side)
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
            }

            key_frame_images = result.get("key_frame_images") or {}
            if isinstance(key_frame_images, dict):
                for event_name, name in key_frame_images.items():
                    if isinstance(name, str) and name:
                        job_result["key_frame_images"][event_name] = (
                            f"/mvp/artifacts/{result['run_id']}/{name}"
                        )

            self._build_overlay_artifact(job_id, result, video_path, job_result)
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
                phase_detector = PhaseDetector(fps=fps)
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

