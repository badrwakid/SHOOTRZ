"""MVP API router (thin layer over service orchestration)."""

from typing import Optional
import json

import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ..contracts.mvp import MVPAnalyzeQueuedResponse, MVPResultResponse
from ..inference.phase_detector import PhaseDetector
from ..inference.pose_2d import BASKETBALL_KEYPOINTS
from ..services.mvp_job_service import MVPJobService


router = APIRouter(prefix="/mvp", tags=["mvp"])
service = MVPJobService()


@router.post("/analyze", response_model=MVPAnalyzeQueuedResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    shooting_side: Optional[str] = "auto"
):
    return service.queue_job(background_tasks, file, shooting_side or "auto")


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

    return FileResponse(
        path=str(artifact_path),
        media_type=media_type,
        filename=filename
    )


@router.get("/test-phase-detection/{run_id}")
async def test_phase_detection(run_id: str):
    """
    Debug endpoint to verify motion-based phase detection is working on a given run.
    Reads pose_keypoints.json from outputs/{run_id} and runs PhaseDetector.
    """
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
                {
                    "frame_idx": frame_idx,
                    "landmarks": landmarks,
                    "confidence": confidence,
                }
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
            detail={
                "success": False,
                "run_id": run_id,
                "error": str(e),
            },
        )
