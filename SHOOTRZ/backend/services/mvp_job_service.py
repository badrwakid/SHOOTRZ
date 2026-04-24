from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional, Set

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


_MAX_WORKERS = int(os.getenv("SHOOTRZ_WORKERS", str(max(1, (os.cpu_count() or 2) - 1))))
_JOB_TIMEOUT_S = int(os.getenv("SHOOTRZ_JOB_TIMEOUT_S", "120"))
# How long to WAIT for the AI coach (Gemini) before falling back to the
# rule-based score. 0 restores the pre-2026-04-23 fire-and-forget behaviour.
_AI_TIMEOUT_S = float(os.getenv("SHOOTRZ_AI_TIMEOUT_S", "10"))


def _env_overlay_flag() -> Optional[bool]:
    """Read the overlay env override. ``None`` means 'defer to YAML'."""
    raw = os.getenv("SHOOTRZ_SAVE_OVERLAY")
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_save_overlay() -> bool:
    """Combine the env override with the YAML ``output.save_overlay_video``.

    Prior to 2026-04-23 the async job path consulted ONLY the env var, so
    flipping ``save_overlay_video: true`` in ``mvp_config.yaml`` had no effect
    on the production pipeline. This helper is the single source of truth.
    """
    env_val = _env_overlay_flag()
    if env_val is not None:
        return env_val
    try:
        from ..mvp.core.config_loader import load_config  # local to avoid cycle
        cfg = load_config()
        return bool(cfg.get("output.save_overlay_video", False))
    except Exception:
        return False


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


def _worker_warmup() -> None:
    """Run once per ProcessPool worker so the first job doesn't pay cold-start costs.

    Importing the top-level ``mediapipe`` package pulls in ``mediapipe.tasks``
    which in turn loads tensorflow — and in some environments tensorflow's
    protobuf runtime is out of sync. The pipeline only needs
    ``mediapipe.solutions.pose`` (used via ``MediaPipePoseDetector``), so we
    warm that import path and avoid the tensorflow chain entirely.
    """
    try:
        import socket

        socket.setdefaulttimeout(5)
    except Exception:
        pass
    try:
        from mediapipe import solutions as _mp_solutions  # noqa: F401

        _ = _mp_solutions.pose  # triggers model file extraction
    except Exception as exc:
        logger.warning("Worker warmup: mediapipe.solutions.pose unavailable: %s", exc)


def _run_pipeline_sync(video_path: str, shooting_side: str, save_overlay: bool) -> Dict[str, Any]:
    """Top-level (picklable) callable executed inside a worker subprocess."""
    pipeline = MVPPipeline()
    proc = psutil.Process(os.getpid())
    mem_before_mb = proc.memory_info().rss / 1024 ** 2
    t_start = time.perf_counter()
    result = pipeline.process_video(
        video_path,
        shooting_side,
        peak_memory_sampler=lambda: proc.memory_info().rss / 1024 ** 2,
        save_overlay=save_overlay,
    )
    elapsed_s = time.perf_counter() - t_start
    mem_after_mb = proc.memory_info().rss / 1024 ** 2
    result["_worker_diagnostics"] = {
        "elapsed_s": round(elapsed_s, 3),
        "memory_before_mb": round(mem_before_mb, 1),
        "memory_after_mb": round(mem_after_mb, 1),
        "worker_pid": os.getpid(),
    }
    return result


class MVPJobService:
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.outputs_dir = self.backend_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.job_store = DurableJobStore(self.outputs_dir / "jobs.sqlite3", retention_hours=72)
        self.artifact_retention_days = 7

        self._executor: Optional[ProcessPoolExecutor] = None
        self._running_tasks: Set[asyncio.Task] = set()

    # ------------------------------------------------------------------
    # Executor lifecycle
    # ------------------------------------------------------------------

    def _get_executor(self) -> ProcessPoolExecutor:
        if self._executor is None:
            self._executor = ProcessPoolExecutor(
                max_workers=_MAX_WORKERS,
                initializer=_worker_warmup,
            )
            logger.info("Spawned ProcessPoolExecutor (workers=%s)", _MAX_WORKERS)
        return self._executor

    def shutdown(self) -> None:
        if self._executor is not None:
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                logger.exception("Executor shutdown error")
            self._executor = None

    # ------------------------------------------------------------------
    # Queue API
    # ------------------------------------------------------------------

    def queue_job(
        self,
        background_tasks: BackgroundTasks,
        upload: UploadFile,
        shooting_side: str = "auto",
    ) -> MVPAnalyzeQueuedResponse:
        """Legacy BackgroundTasks path — kept so non-async callers still work."""
        job_id, video_path = self._persist_upload(upload)
        self.job_store.upsert(job_id, {"status": "queued"})
        background_tasks.add_task(self._process_video_job, job_id, video_path, shooting_side)
        logger.info("Queued MVP analysis job (BackgroundTasks)", extra={"job_id": job_id})
        return MVPAnalyzeQueuedResponse(job_id=job_id, status="queued")

    async def queue_job_async(
        self,
        upload: UploadFile,
        shooting_side: str = "auto",
        user_id: Optional[str] = None,
    ) -> MVPAnalyzeQueuedResponse:
        """Non-blocking queue: spawns a ProcessPool task the event loop can forget."""
        job_id, video_path = self._persist_upload(upload)
        self.job_store.upsert(job_id, {"status": "queued", "user_id": user_id})
        task = asyncio.create_task(
            self._process_video_job_async(job_id, video_path, shooting_side, user_id=user_id)
        )
        self._running_tasks.add(task)
        task.add_done_callback(self._running_tasks.discard)
        logger.info("Queued MVP analysis job (ProcessPool)", extra={"job_id": job_id})
        return MVPAnalyzeQueuedResponse(job_id=job_id, status="queued")

    def _persist_upload(self, upload: UploadFile) -> tuple[str, str]:
        job_id = generate_job_id()
        suffix = Path(upload.filename).suffix if upload.filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(upload.file, tmp_file)
            video_path = tmp_file.name
        self.job_store.cleanup_expired()
        self.cleanup_old_outputs()
        return job_id, video_path

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

    # ------------------------------------------------------------------
    # Async job driver (ProcessPool)
    # ------------------------------------------------------------------

    async def _process_video_job_async(
        self,
        job_id: str,
        video_path: str,
        shooting_side: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Event-loop-friendly job driver.

        Every synchronous/blocking step below is wrapped with
        :func:`asyncio.to_thread` so the FastAPI event loop keeps serving
        ``GET /api/mvp/result/{job_id}`` polls while the pipeline / LLM /
        Supabase writes run. The 2026-04-23 timeout incident was caused by
        inline sync calls here blocking every concurrent request for 20-40s.
        """
        self._set_status(job_id, {"status": "processing"})
        save_overlay = _resolve_save_overlay()
        # Flag used by ``finally`` so we don't delete the upload while the
        # off-loop overlay builder still needs it.
        delete_upload = True
        try:
            executor = self._get_executor()
            loop = asyncio.get_running_loop()
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor,
                        partial(_run_pipeline_sync, video_path, shooting_side, save_overlay),
                    ),
                    timeout=float(_JOB_TIMEOUT_S),
                )
            except asyncio.TimeoutError:
                logger.warning("Job timed out", extra={"job_id": job_id})
                self._set_status(
                    job_id,
                    {
                        "status": "failed",
                        "error": "Analysis timed out. Please try a shorter or simpler clip.",
                        "error_detail": f"timeout after {_JOB_TIMEOUT_S}s",
                        "error_type": "TimeoutError",
                    },
                )
                return
            except Exception as exc:
                logger.exception("Pipeline subprocess failed", extra={"job_id": job_id})
                self._finalize_failure(job_id, exc)
                return

            # Build the initial payload with rule-based feedback, then snapshot
            # it as a "processing" update so clients polling /result/{jobId}
            # see progress (but NOT a spurious "completed" with a rule-based
            # score that we're about to overwrite). Offloaded to threads so
            # the event loop keeps serving polls.
            job_result = await asyncio.to_thread(
                self._build_completed_payload, job_id, result
            )
            await asyncio.to_thread(
                self._maybe_build_overlay, job_id, result, video_path, job_result, save_overlay
            )

            # AWAIT Gemini (within a timeout) so the final status=completed
            # payload carries the AI score + coach-style feedback. If Gemini
            # hangs/fails we fall back to the rule-based score untouched.
            # asyncio.to_thread keeps the event loop responsive while the SDK
            # is doing its blocking HTTPS call.
            if _AI_TIMEOUT_S > 0:
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(self._enrich_with_gemini, job_result),
                        timeout=_AI_TIMEOUT_S,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Gemini enrichment timed out after %ss; shipping rule-based score",
                        _AI_TIMEOUT_S,
                        extra={"job_id": job_id},
                    )
                except Exception:
                    logger.exception(
                        "Gemini enrichment raised; shipping rule-based score",
                        extra={"job_id": job_id},
                    )

            self._set_status(job_id, job_result)
            logger.info(
                "Job completed",
                extra={
                    "job_id": job_id,
                    "overall_score": job_result.get("overall_score"),
                    "rule_based_score": job_result.get("rule_based_score"),
                    "ai_scored": job_result.get("ai_scored"),
                },
            )

            # Supabase persist stays fire-and-forget — it never gates what the
            # client sees.
            delete_upload = False
            asyncio.create_task(
                self._persist_supabase_and_cleanup(job_id, job_result, video_path, user_id=user_id)
            )
        finally:
            if delete_upload:
                try:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                except Exception:
                    logger.warning("Failed to remove temporary upload", extra={"job_id": job_id})

    async def _persist_supabase_and_cleanup(
        self,
        job_id: str,
        job_result: Dict[str, Any],
        video_path: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Persist to Supabase off the event loop. Never invalidates the
        already-stored ``completed`` result."""
        try:
            try:
                await asyncio.to_thread(self._save_to_supabase, job_id, job_result)
                self._set_status(job_id, job_result)
            except Exception:
                logger.exception("Supabase persist failed", extra={"job_id": job_id})

            # Auto-persist to user account if upload was authenticated
            if user_id and job_result.get("status") == "completed":
                try:
                    await asyncio.to_thread(self.save_result_for_user, job_id, user_id)
                    logger.info("Auto-persisted analysis to Supabase", extra={"job_id": job_id, "user_id": user_id})
                except Exception:
                    logger.exception("Auto-persist to Supabase failed", extra={"job_id": job_id})
        finally:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                logger.warning(
                    "Failed to remove temporary upload after enrichment",
                    extra={"job_id": job_id},
                )

    # ------------------------------------------------------------------
    # Synchronous driver (legacy path — also used by tests)
    # ------------------------------------------------------------------

    def _process_video_job(self, job_id: str, video_path: str, shooting_side: str = "auto") -> None:
        self._set_status(job_id, {"status": "processing"})
        save_overlay = _resolve_save_overlay()
        try:
            result = _run_pipeline_sync(video_path, shooting_side, save_overlay)
            job_result = self._build_completed_payload(job_id, result)
            self._maybe_build_overlay(job_id, result, video_path, job_result, save_overlay)
            self._set_status(job_id, job_result)
            try:
                self._enrich_with_gemini(job_result)
                self._save_to_supabase(job_id, job_result)
                self._set_status(job_id, job_result)
            except Exception:
                logger.exception("Post-processing enrichment failed", extra={"job_id": job_id})
        except Exception as exc:
            self._finalize_failure(job_id, exc)
        finally:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                logger.warning("Failed to remove temporary upload", extra={"job_id": job_id})

    # ------------------------------------------------------------------
    # Result assembly
    # ------------------------------------------------------------------

    def _build_completed_payload(self, job_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        status = result.get("status") or "completed"
        if status == "completed_low_quality":
            return self._build_low_quality_payload(result)

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

        worker_diag = result.get("_worker_diagnostics") or {}
        elapsed_s = float(worker_diag.get("elapsed_s") or 0.0)
        peak_mem_mb = max(
            float(worker_diag.get("memory_before_mb") or 0.0),
            float(worker_diag.get("memory_after_mb") or 0.0),
            float(result.get("peak_memory_mb") or 0.0),
        )

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
                "overlay_video": None,
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
            "peak_memory_mb": round(peak_mem_mb, 1) if peak_mem_mb else None,
            "pose_overall_confidence": result.get("pose_overall_confidence"),
            "low_light": bool(result.get("low_light", False)),
        }

        # Persist run metadata for reproducibility.
        try:
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
                    "peak_memory_mb": round(peak_mem_mb, 1) if peak_mem_mb else None,
                    "pose_overall_confidence": result.get("pose_overall_confidence"),
                }
            )
            with open(run_meta_path, "w", encoding="utf-8") as wf:
                json.dump(clean_nan_for_json(run_meta), wf, indent=2)
        except Exception:
            logger.warning("Could not update run_metadata.json", extra={"job_id": job_id})

        return job_result

    def _build_low_quality_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "completed_low_quality",
            "contract_version": CONTRACT_VERSION,
            "run_id": result.get("run_id"),
            "metrics": [],
            "overall_score": 0,
            "feedback_summary": result.get("feedback_summary", "Video quality too low for analysis."),
            "feedback_bullets": result.get("feedback_bullets") or [],
            "score_components": [],
            "shot_window": {},
            "events": {},
            "shooting_side": result.get("shooting_side", "right"),
            "angles_data": {"frames": [], "timestamps": [], "elbow": [], "knee": [], "wrist": []},
            "artifacts": {
                "overlay_video": None,
                "angles_csv": None,
                "report_json": None,
                "event_candidates": None,
                "event_confidence": None,
                "feature_table": None,
                "signals_smoothed": None,
                "warnings": None,
            },
            "key_frame_images": {},
            "quality_warnings": result.get("quality_warnings", []),
            "diagnostics": result.get("diagnostics", {}),
            "processing_time_seconds": 0.0,
            "phase_timings_seconds": result.get("phase_timings_seconds", {}),
            "peak_memory_mb": None,
            "pose_overall_confidence": result.get("pose_overall_confidence"),
            "low_light": bool(result.get("low_light", False)),
        }

    def _finalize_failure(self, job_id: str, exc: BaseException) -> None:
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

    # ------------------------------------------------------------------
    # Gemini + Supabase enrichment (deferred, best-effort)
    # ------------------------------------------------------------------

    def _enrich_with_gemini(self, job_result: Dict[str, Any]) -> None:
        """Replace the rule-based score + feedback with the Gemini coach output.

        Post-2026-04-23 Gemini returns:
        * ``ai_overall_score`` (0-100) - the holistic grade.
        * ``ai_score_rationale`` - one-line justification.
        * ``overall_explanation``, ``feedback_bullets``, ``metric_explanations``.

        Rule-based number is preserved on ``job_result["rule_based_score"]``
        so the UI / debug endpoints can show "AI vs rule" if desired.
        Any Gemini failure keeps the rule-based score untouched.
        """
        if job_result.get("status") != "completed":
            return

        rule_based_score = int(job_result.get("overall_score", 0) or 0)
        job_result["rule_based_score"] = rule_based_score

        tier = "poor"
        if rule_based_score >= 90:
            tier = "elite"
        elif rule_based_score >= 75:
            tier = "great"
        elif rule_based_score >= 60:
            tier = "good"
        elif rule_based_score >= 40:
            tier = "fair"

        try:
            fb_result = llm_service.get_shot_feedback(
                metrics=job_result.get("metrics", []),
                score_components=job_result.get("score_components", []),
                overall_score=rule_based_score,
                score_tier=tier,
                feedback_summary=job_result.get("feedback_summary", ""),
                feedback_bullets=job_result.get("feedback_bullets", []),
            )
        except Exception:
            logger.warning("Gemini enrichment skipped, using rule-based feedback", exc_info=True)
            job_result["gemini_enriched"] = False
            return

        # ``get_shot_feedback`` returns (output, is_fallback). The is_fallback
        # flag tells us "Gemini was down and you're looking at the rule-based
        # echo" - in that case don't mark ai_scored=True.
        if isinstance(fb_result, tuple) and len(fb_result) == 2:
            fb, is_fallback = fb_result
        else:
            fb, is_fallback = fb_result, False

        ai_score = getattr(fb, "ai_overall_score", None)
        score_valid = isinstance(ai_score, int) and 0 <= ai_score <= 100
        if score_valid and not is_fallback:
            job_result["overall_score"] = ai_score
            job_result["ai_score_rationale"] = getattr(fb, "ai_score_rationale", "")
            job_result["ai_scored"] = True
        else:
            job_result["ai_scored"] = False
            if is_fallback:
                job_result["ai_score_rationale"] = (
                    "AI coach was unavailable; showing rule-based score."
                )

        job_result["feedback_summary"] = fb.overall_explanation or job_result.get(
            "feedback_summary", ""
        )
        if fb.feedback_bullets:
            job_result["feedback_bullets"] = fb.feedback_bullets

        for m in job_result.get("metrics", []):
            for me in fb.metric_explanations:
                if me.metric_name == m.get("name"):
                    m["explanation"] = me.explanation
                    break

        job_result["gemini_strengths"] = fb.strengths
        job_result["gemini_improvements"] = fb.improvements
        job_result["gemini_enriched"] = True
        logger.info(
            "Shot feedback enriched with Gemini",
            extra={
                "rule_based_score": rule_based_score,
                "ai_overall_score": ai_score,
            },
        )

    def _save_to_supabase(self, job_id: str, job_result: Dict[str, Any]) -> None:
        if job_result.get("status") != "completed":
            return
        try:
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
            if session_summary and session_summary.key_takeaway:
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
            logger.info(
                "Analysis summary prepared for Supabase",
                extra={"job_id": job_id, "tier": tier, "score": overall},
            )
        except Exception:
            logger.exception("Failed to prepare Supabase summary", extra={"job_id": job_id})

    def save_result_for_user(
        self, job_id: str, user_id: str,
    ) -> Optional[Dict[str, Any]]:
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
            return out
        except Exception:
            logger.exception("Failed to save results to Supabase", extra={"job_id": job_id})
            return None

    # ------------------------------------------------------------------
    # Maintenance + overlay
    # ------------------------------------------------------------------

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

    def _maybe_build_overlay(
        self,
        job_id: str,
        result: Dict[str, Any],
        video_path: str,
        job_result: Dict[str, Any],
        save_overlay: bool,
    ) -> None:
        """Render the skeleton overlay when ``save_overlay`` is set.

        The pipeline already hands us ``result['phases']`` and
        ``pose_keypoints.json`` so we never re-run :class:`PhaseDetector` or
        re-decode the clip beyond what :func:`annotate_video` needs.

        Passes the shot window, per-metric selected_frame markers and an
        angle HUD spec so the overlay clearly shows which frame the score
        was measured at and what value was read.
        """
        if not save_overlay:
            job_result["artifacts"]["overlay_video"] = None
            return
        if result.get("status") not in {"completed", "completed_low_quality"}:
            job_result["artifacts"]["overlay_video"] = None
            return

        try:
            pose_json_path = Path(result["output_dir"]) / "pose_keypoints.json"
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

            # Prefer the phases the pipeline already computed. Fall back to
            # re-running PhaseDetector only if the pipeline didn't provide them
            # (e.g. older cached results).
            phases = list(result.get("phases") or [])
            if not phases:
                fps = pose_json.get("video_metadata", {}).get("fps", 30.0)
                phase_detector = PhaseDetector(
                    fps=fps,
                    shooting_side=result.get("shooting_side", "right"),
                )
                phases = phase_detector.detect_phases(pose_results) or []

            # HUD + marker inputs derived from the primitive metric payload.
            shot_window = result.get("shot_window") or {}
            raw_metrics = result.get("metrics") or []
            score_breakdown = {
                entry.get("metric"): entry.get("sub_score")
                for entry in (result.get("diagnostics", {}).get("score_component_summary") or [])
                if isinstance(entry, dict)
            }
            hud_label_map = {
                "elbow_extension": "Elbow",
                "knee_bend": "Knee",
                "wrist_follow_through": "Wrist change",
            }
            metric_hud = [
                {
                    "label": hud_label_map.get(m.get("name"), str(m.get("name", "metric"))),
                    "value_deg": (
                        float(m.get("value"))
                        if m.get("verdict") != "Low Confidence"
                        else None
                    ),
                    "score": score_breakdown.get(m.get("name")),
                }
                for m in raw_metrics
                if m.get("name") in hud_label_map
            ]
            metric_markers: Dict[int, str] = {}
            for m in raw_metrics:
                sf = m.get("selected_frame")
                if isinstance(sf, int):
                    metric_markers[int(sf)] = (
                        hud_label_map.get(m.get("name"), "MEASURED").upper()
                    )

            annotate_video(
                video_path=overlay_video_path,
                pose_results=pose_results,
                phases=phases,
                output_path=str(overlay_path),
                fps=pose_json.get("video_metadata", {}).get("fps", 30.0),
                shot_window=shot_window,
                metric_hud=metric_hud,
                metric_markers=metric_markers,
            )
            if overlay_path.exists():
                job_result["artifacts"]["overlay_video"] = (
                    f"/mvp/artifacts/{result['run_id']}/overlay.mp4"
                )
                job_result["phase_detector_version"] = (
                    "pipeline_precomputed" if result.get("phases") else "fallback_inline"
                )
                job_result["phase_detected_at"] = time.time()
        except Exception as overlay_error:
            logger.exception(
                "Overlay generation failed",
                extra={"job_id": job_id, "run_id": result.get("run_id"), "error": str(overlay_error)},
            )
            job_result["artifacts"]["overlay_video"] = None
