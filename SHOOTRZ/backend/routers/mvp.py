"""MVP API router (thin layer over service orchestration).

Concurrency model:
    * ``slowapi`` enforces a per-IP request budget.
    * ``_analysis_semaphore`` bounds total in-flight pipeline jobs; when full
      we 429 immediately rather than buffering requests behind a blocked
      event loop.
    * The semaphore is HELD for the job lifetime via an asyncio-safe
      background task so the cap actually limits real throughput (the old
      acquire-then-release pattern only gated the handshake).
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..contracts.mvp import MVPAnalyzeQueuedResponse, MVPResultResponse
from ..inference.phase_detector import PhaseDetector
from ..inference.pose_2d import BASKETBALL_KEYPOINTS
from ..services.mvp_job_service import MVPJobService


router = APIRouter(prefix="/mvp", tags=["mvp"])
service = MVPJobService()
limiter = Limiter(key_func=get_remote_address)

_MAX_CONCURRENT = int(os.getenv("SHOOTRZ_MAX_CONCURRENT", "8"))
_analysis_semaphore = asyncio.Semaphore(_MAX_CONCURRENT)


def _max_upload_bytes() -> int:
    """Return the upload size cap in bytes, reading the env var on every call.

    Reading at request time (not module import time) lets tests override the
    cap via ``monkeypatch.setenv("SHOOTRZ_MAX_UPLOAD_MB", ...)`` without
    needing ``importlib.reload``. The default is 200 MB.
    """
    return int(os.getenv("SHOOTRZ_MAX_UPLOAD_MB", "200")) * 1024 * 1024

# Small process-local cache: maps ``sha256(first 1MB of upload)`` to the job
# id that already analysed the same bytes. Keeps the demo cheap when the same
# clip is submitted twice in a row (e.g. rapid double-tap on the mobile app).
_MAX_CACHE_ENTRIES = 64
_MIN_PREFLIGHT_FRAMES = 30
_result_cache: Dict[str, str] = {}


def _preflight_video(video_path: str) -> Tuple[int, float]:
    """Cheap metadata probe. Raises 400 when the clip is obviously unusable."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Video file could not be opened.")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    cap.release()
    if frame_count < _MIN_PREFLIGHT_FRAMES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Video too short: {frame_count} frames "
                f"(need \u2265 {_MIN_PREFLIGHT_FRAMES}, ~1s at 30fps)"
            ),
        )
    return frame_count, fps


async def _remember_and_run(job_id: str, cache_key: Optional[str]) -> None:
    """Hold the concurrency semaphore for the entire job lifetime."""
    try:
        while True:
            await asyncio.sleep(0.75)
            payload = service.job_store.get(job_id)
            if not payload:
                return
            status = payload.get("status")
            if status in {"completed", "completed_low_quality", "failed"}:
                if cache_key and status in {"completed", "completed_low_quality"}:
                    if len(_result_cache) >= _MAX_CACHE_ENTRIES:
                        _result_cache.pop(next(iter(_result_cache)), None)
                    _result_cache[cache_key] = job_id
                return
    finally:
        _analysis_semaphore.release()


@router.post("/analyze", response_model=MVPAnalyzeQueuedResponse)
@limiter.limit("30/minute")
async def analyze_video(
    request: Request,
    file: UploadFile = File(...),
    shooting_side: str = Query(default="auto"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Queue a video for analysis.

    Fast-fails with 429 when the ProcessPool is saturated so clients can retry
    with back-off instead of piling up in the event loop.
    """
    if _analysis_semaphore.locked():
        raise HTTPException(status_code=429, detail="server_busy_retry")

    # Peek the first 1MB to compute a cheap cache key BEFORE spilling to disk.
    first_mb = await file.read(1024 * 1024)
    cache_key: Optional[str] = None
    if first_mb:
        cache_key = hashlib.sha256(first_mb).hexdigest()
        cached_job = _result_cache.get(cache_key)
        if cached_job:
            payload = service.job_store.get(cached_job)
            if payload and payload.get("status") in {"completed", "completed_low_quality"}:
                return MVPAnalyzeQueuedResponse(job_id=cached_job, status="queued")

    # Spill to a named temp file, prefixed with the already-read bytes. The
    # service still takes an ``UploadFile`` so we wrap the file back up.
    tmp_suffix = Path(file.filename).suffix if file.filename else ".mp4"
    max_bytes = _max_upload_bytes()
    total_read = len(first_mb)
    with NamedTemporaryFile(delete=False, suffix=tmp_suffix) as tmp:
        if first_mb:
            tmp.write(first_mb)
        # Drain the rest of the upload, enforcing the size cap chunk-by-chunk.
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > max_bytes:
                tmp.close()
                try:
                    os.remove(tmp.name)
                except OSError:
                    pass
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File exceeds {max_bytes // 1024 // 1024}MB limit."
                    ),
                )
            tmp.write(chunk)
        tmp_path = tmp.name

    # ``cv2.VideoCapture`` blocks for ~100-500ms on phone clips. Offload to
    # a thread so we don't freeze the event loop while every other client
    # is trying to poll ``/api/mvp/result/...``.
    try:
        await asyncio.to_thread(_preflight_video, tmp_path)
    except HTTPException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    # Acquire the concurrency slot AFTER preflight so rejects don't drain the
    # budget. ``acquire`` never blocks because we bail early when locked.
    try:
        await asyncio.wait_for(_analysis_semaphore.acquire(), timeout=0.1)
    except asyncio.TimeoutError as exc:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise HTTPException(status_code=429, detail="server_busy_retry") from exc

    # Extract user_id from token (optional — anonymous uploads still work)
    user_id: Optional[str] = None
    if authorization:
        try:
            from ..utils.supabase_auth import get_authenticated_user
            auth_user = get_authenticated_user(authorization)
            user_id = auth_user.user_id
        except Exception:
            pass  # Continue as anonymous

    try:
        # Feed the service an object that quacks like UploadFile so it can
        # keep its existing _persist_upload helper.
        wrapped = _RewoundUpload(tmp_path, filename=file.filename or "upload.mp4")
        response = await service.queue_job_async(wrapped, shooting_side or "auto", user_id=user_id)
    except Exception:
        _analysis_semaphore.release()
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    asyncio.create_task(_remember_and_run(response.job_id, cache_key))
    return response


@router.get("/result/{job_id}", response_model=MVPResultResponse)
async def get_result(job_id: str):
    return service.get_result(job_id)


@router.get("/artifacts/{run_id}/{filename}")
async def get_artifact(run_id: str, filename: str):
    artifact_path = service.get_artifact_path(run_id, filename)

    media_types = {
        ".mp4": "video/mp4",
        ".csv": "text/csv",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    media_type = media_types.get(artifact_path.suffix, "application/octet-stream")
    return FileResponse(path=str(artifact_path), media_type=media_type, filename=filename)


@router.get("/test-phase-detection/{run_id}")
async def test_phase_detection(run_id: str):
    """Debug endpoint — runs motion-based phase detection on stored pose keypoints."""
    try:
        pose_json_path = service.outputs_dir / run_id / "pose_keypoints.json"
        if not pose_json_path.exists():
            raise HTTPException(status_code=404, detail=f"pose_keypoints.json not found for run_id={run_id}")

        with open(pose_json_path, "r") as f:
            pose_json = json.load(f)

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

        if not pose_results:
            raise HTTPException(status_code=400, detail="pose_results is empty")

        fps = pose_json.get("video_metadata", {}).get("fps", 30.0)
        phase_detector = PhaseDetector(fps=fps)
        phases = phase_detector.detect_phases(pose_results)

        return {
            "success": True,
            "run_id": run_id,
            "phase_count": len(phases),
            "phases": phases,
            "fps": fps,
            "landmarks_shape": list(pose_results[0]["landmarks"].shape),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "run_id": run_id, "error": str(e)},
        )


class _RewoundUpload:
    """Minimal UploadFile stand-in that streams from an already-spilled temp file."""

    def __init__(self, path: str, filename: str):
        self.filename = filename
        self._path = path
        self.file = open(path, "rb")

    def close(self) -> None:
        try:
            self.file.close()
        except Exception:
            pass
