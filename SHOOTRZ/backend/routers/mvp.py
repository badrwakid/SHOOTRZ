"""
FastAPI endpoints for MVP analysis.

Provides:
- POST /mvp/analyze - Upload video for analysis
- GET /mvp/result/{job_id} - Get analysis results
- GET /mvp/artifacts/{run_id}/{filename} - Download artifacts
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import shutil
import json
import pandas as pd
import numpy as np
import time
import traceback

import sys
from pathlib import Path as PathLib
import logging

# Add backend to path for imports
backend_path = PathLib(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.pipeline import MVPPipeline
from utils.id_gen import generate_job_id
from utils.video_annotator import annotate_video
from inference.pose_2d import BASKETBALL_KEYPOINTS
from inference.phase_detector import PhaseDetector

router = APIRouter(prefix="/mvp", tags=["mvp"])
logger = logging.getLogger(__name__)

# In-memory job store (use Redis in production)
job_store: Dict[str, Dict[str, Any]] = {}


def clean_nan_for_json(obj: Any) -> Any:
    """
    Recursively clean data for JSON serialization.
    Handles: NaN, Infinity, NumPy types, Path objects
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle NumPy/Pandas types
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        # Check for NaN or Infinity
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [clean_nan_for_json(item) for item in obj.tolist()]
    
    # Handle Python floats
    elif isinstance(obj, float):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    
    # Handle Path objects
    elif isinstance(obj, Path):
        return str(obj)
    
    # Handle collections
    elif isinstance(obj, dict):
        return {k: clean_nan_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_nan_for_json(item) for item in obj]
    
    # Handle other types (int, str, bool, etc.)
    else:
        return obj


def _process_video_job(
    job_id: str,
    video_path: str,
    shooting_side: str = "auto"
):
    """Background task to process video."""
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:37",
            "message": "_process_video_job entry",
            "data": {"job_id": job_id, "video_path": video_path, "shooting_side": shooting_side},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "G"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    try:
        # Update status
        if job_id not in job_store:
            job_store[job_id] = {}
        job_store[job_id]["status"] = "processing"
        
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:55",
                "message": "Starting pipeline",
                "data": {"job_id": job_id},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
        # Run pipeline
        pipeline = MVPPipeline()
        result = pipeline.process_video(video_path, shooting_side)
        
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:70",
                "message": "Pipeline completed",
                "data": {"job_id": job_id, "run_id": result.get("run_id"), "output_dir": result.get("output_dir")},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
        # Load angles data for React Native
        angles_csv = Path(result["output_dir"]) / "angles.csv"
        if not angles_csv.exists():
            raise FileNotFoundError(f"Angles CSV not found: {angles_csv}")
        
        angles_df = pd.read_csv(angles_csv)
        
        # Replace NaN values with None for JSON serialization
        angles_data = {
            "frames": angles_df["frame_id"].fillna(0).astype(int).tolist(),
            "timestamps": angles_df["timestamp"].fillna(0.0).tolist(),
            "elbow": [None if pd.isna(x) else float(x) for x in angles_df["elbow_angle"]],
            "knee": [None if pd.isna(x) else float(x) for x in angles_df["knee_angle"]],
            "wrist": [None if pd.isna(x) else float(x) for x in angles_df["wrist_angle"]],
        }
        
        # Validate and prepare result data
        try:
            # Ensure overall_score is valid
            overall_score = result.get("overall_score", 0)
            if pd.isna(overall_score) or np.isnan(overall_score) or overall_score < 0:
                overall_score = 0
            elif overall_score > 100:
                overall_score = 100
            
            # Ensure metrics is a list
            metrics = result.get("metrics", [])
            if not isinstance(metrics, list):
                metrics = []
            
            # Update job store with results
            job_result = {
                "status": "completed",
                "run_id": result["run_id"],
                "metrics": metrics,
                "overall_score": int(overall_score),
                "feedback_summary": result.get("feedback_summary", "Analysis completed successfully"),
                "shot_window": result.get("shot_window", {}),
                "shooting_side": result.get("shooting_side", "right"),
                "angles_data": angles_data,
                "artifacts": {
                    "overlay_video": f"/mvp/artifacts/{result['run_id']}/overlay.mp4",
                    "angles_csv": f"/mvp/artifacts/{result['run_id']}/angles.csv",
                    "report_json": f"/mvp/artifacts/{result['run_id']}/report.json",
                },
                "quality_warnings": result.get("quality_warnings", []),
            }
            
            # Clean all NaN/Infinity/NumPy types for JSON serialization
            job_store[job_id] = clean_nan_for_json(job_result)
            
            # Generate annotated video overlay (best-effort)
            try:
                pose_json_path = Path(result["output_dir"]) / "pose_keypoints.json"
                shot_window_path = Path(result["output_dir"]) / "shot_window.json"
                overlay_path = Path(result["output_dir"]) / "overlay.mp4"
                input_video_path = Path(result["output_dir"]) / "input_video.mp4"
                overlay_video_path = str(input_video_path) if input_video_path.exists() else str(video_path)
                
                logger.info(
                    "Overlay generation start",
                    extra={
                        "job_id": job_id,
                        "run_id": result["run_id"],
                        "video_path": overlay_video_path,
                        "overlay_path": str(overlay_path),
                    },
                )

                # Also log to .cursor/debug.log (survives console capture issues)
                try:
                    log_data = {
                        "location": "mvp.py:overlay",
                        "message": "Overlay generation start",
                        "data": {
                            "job_id": job_id,
                            "run_id": result.get("run_id"),
                            "overlay_path": str(overlay_path),
                            "video_path_used": overlay_video_path,
                            "has_input_video_copy": input_video_path.exists(),
                        },
                        "timestamp": int(time.time() * 1000),
                    }
                    with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                
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
                    
                    pose_results.append({
                        "frame_idx": frame_idx,
                        "landmarks": landmarks,
                        "confidence": confidence
                    })
                
                # Use new motion-based phase detector with validation and detailed logging
                phases = []
                try:
                    # Validate pose_results format
                    if not pose_results:
                        raise ValueError("pose_results is empty - cannot detect phases")
                    first_result = pose_results[0]
                    if "landmarks" not in first_result:
                        raise ValueError("pose_results missing 'landmarks' key")
                    landmarks_shape = first_result["landmarks"].shape
                    logger.info(
                        "Phase detection input ready",
                        extra={
                            "run_id": result.get("run_id"),
                            "frames": len(pose_results),
                            "landmarks_shape": landmarks_shape,
                        },
                    )
                    if landmarks_shape[0] < 33:
                        logger.warning(
                            "Landmarks count is less than 33 (got %s)",
                            landmarks_shape[0],
                        )

                    # Run detector
                    fps = pose_json.get("video_metadata", {}).get("fps", 30.0)
                    logger.info(
                        "Starting phase detection",
                        extra={
                            "run_id": result.get("run_id"),
                            "fps": fps,
                            "frames": len(pose_results),
                        },
                    )
                    phase_detector = PhaseDetector(fps=fps)
                    phases = phase_detector.detect_phases(pose_results)

                    # Verify results are from new detector
                    if phases:
                        phase_names = [p.get("phase") for p in phases]
                        has_peak = any("peak_frame" in p for p in phases)
                        logger.info(
                            "Phase detection success",
                            extra={
                                "run_id": result.get("run_id"),
                                "phase_count": len(phases),
                                "phases": phase_names,
                                "has_peak_frame": has_peak,
                            },
                        )
                        if "start" in phase_names:
                            raise ValueError("Phase detection returned old format ('start' phase present)")
                        if not has_peak:
                            logger.warning("Phases missing peak_frame; ensure new detector is used")
                        # Track detector version and timestamp
                        job_store[job_id]["phase_detector_version"] = "motion_based_v2"
                        job_store[job_id]["phase_detected_at"] = time.time()
                    else:
                        logger.warning("Phase detector returned empty phases")
                except Exception as phase_err:
                    logger.warning(f"Phase detection failed: {phase_err}, using fallback", exc_info=True)
                    # Fallback to old method if phase detector fails
                    if shot_window_path.exists():
                        with open(shot_window_path, "r") as f:
                            sw = json.load(f)
                        phases = [
                            {"phase": "stance", "start_frame": sw.get("start_frame", 0), "end_frame": sw.get("crouch_frame", 0)},
                            {"phase": "crouch", "start_frame": sw.get("crouch_frame", 0), "end_frame": sw.get("release_frame", 0)},
                            {"phase": "release", "start_frame": sw.get("release_frame", 0), "end_frame": sw.get("end_frame", sw.get("release_frame", 0))},
                        ]
                    job_store[job_id]["phase_detector_version"] = "fallback"
                    job_store[job_id]["phase_detected_at"] = time.time()
                
                annotate_video(
                    video_path=overlay_video_path,
                    pose_results=pose_results,
                    phases=phases,
                    output_path=str(overlay_path),
                    fps=pose_json.get("video_metadata", {}).get("fps", 30.0)
                )

                if not overlay_path.exists():
                    raise FileNotFoundError(f"Overlay was not created at: {overlay_path}")
                
                # Update artifacts with overlay
                job_store[job_id]["artifacts"]["overlay_video"] = f"/mvp/artifacts/{result['run_id']}/overlay.mp4"
                logger.info(
                    "Overlay generation complete",
                    extra={"job_id": job_id, "run_id": result["run_id"], "overlay_path": str(overlay_path)},
                )
                try:
                    log_data = {
                        "location": "mvp.py:overlay",
                        "message": "Overlay generation complete",
                        "data": {"job_id": job_id, "run_id": result.get("run_id"), "overlay_path": str(overlay_path)},
                        "timestamp": int(time.time() * 1000),
                    }
                    with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
            except Exception as overlay_err:
                logger.exception(
                    "Overlay generation failed",
                    extra={"job_id": job_id, "run_id": result["run_id"], "error": str(overlay_err)},
                )
                try:
                    log_data = {
                        "location": "mvp.py:overlay",
                        "message": "Overlay generation failed",
                        "data": {"job_id": job_id, "run_id": result.get("run_id"), "error": str(overlay_err)},
                        "timestamp": int(time.time() * 1000),
                    }
                    with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                except Exception:
                    pass
                job_store[job_id]["artifacts"]["overlay_video"] = None
            
        except Exception as e:
            # If result preparation fails, mark as failed
            raise Exception(f"Failed to prepare analysis results: {str(e)}")
        
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:110",
                "message": "Job completed successfully",
                "data": {"job_id": job_id, "status": "completed"},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
    except Exception as e:
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:120",
                "message": "Job failed",
                "data": {"job_id": job_id, "error": str(e), "error_type": type(e).__name__},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
        # Create detailed error message
        error_message = str(e)
        if "FileNotFoundError" in type(e).__name__:
            error_message = "Video file processing failed. Please try recording a new video."
        elif "MediaPipeError" in str(e) or "pose" in str(e).lower():
            error_message = "Could not detect pose in video. Please ensure the shooter is clearly visible."
        elif "angles" in str(e).lower() or "joint" in str(e).lower():
            error_message = "Could not compute shooting angles. Please ensure full body is visible in frame."
        
        job_store[job_id] = clean_nan_for_json({
            "status": "failed",
            "error": error_message,
            "error_detail": str(e),
            "error_type": type(e).__name__,
        })
        
        print(f"Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()


@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    shooting_side: Optional[str] = "auto"
):
    """
    Analyze basketball shooting video.
    
    Args:
        file: Video file (mp4, mov)
        shooting_side: "auto", "left", or "right"
    
    Returns:
        Job ID for polling results
    """
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:90",
            "message": "analyze_video entry",
            "data": {
                "filename": file.filename if file else None,
                "shooting_side": shooting_side,
                "content_type": file.content_type if file else None
            },
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B,C"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    # Generate job ID
    job_id = generate_job_id()
    
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:110",
            "message": "Before file save",
            "data": {"job_id": job_id, "filename": file.filename if file else None},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B,C"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    # Save uploaded file temporarily
    suffix = Path(file.filename).suffix if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        video_path = tmp_file.name
    
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:120",
            "message": "File saved, queueing job",
            "data": {"job_id": job_id, "video_path": video_path, "file_size": Path(video_path).stat().st_size if Path(video_path).exists() else 0},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B,C"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    # Queue processing job
    job_store[job_id] = {"status": "queued"}
    background_tasks.add_task(
        _process_video_job,
        job_id,
        video_path,
        shooting_side
    )
    
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:135",
            "message": "Response returning",
            "data": {"job_id": job_id, "status": "queued"},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B,C"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    return {
        "job_id": job_id,
        "status": "queued"
    }


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get analysis results for a job.
    
    Args:
        job_id: Job ID from /mvp/analyze
    
    Returns:
        Analysis results
    """
    # #region agent log
    try:
        log_data = {
            "location": "mvp.py:203",
            "message": "get_result entry",
            "data": {"job_id": job_id, "job_store_keys": list(job_store.keys())},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "F"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    try:
        if job_id not in job_store:
            # #region agent log
            try:
                log_data = {
                    "location": "mvp.py:220",
                    "message": "Job not found",
                    "data": {"job_id": job_id},
                    "timestamp": int(time.time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "F"
                }
                with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            raise HTTPException(status_code=404, detail="Job not found")
        
        result = job_store[job_id]
        
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:235",
                "message": "Returning result",
                "data": {"job_id": job_id, "status": result.get("status"), "has_error": "error" in result},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "F"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        # #region agent log
        try:
            log_data = {
                "location": "mvp.py:250",
                "message": "get_result error",
                "data": {"job_id": job_id, "error": str(e), "error_type": type(e).__name__},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "F"
            }
            with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving result: {str(e)}")


@router.get("/artifacts/{run_id}/{filename}")
async def get_artifact(run_id: str, filename: str):
    """
    Download artifact file.
    
    Args:
        run_id: Run ID
        filename: Artifact filename
    
    Returns:
        File download
    """
    # Get outputs directory
    backend_dir = Path(__file__).parent.parent
    artifact_path = backend_dir / "outputs" / run_id / filename
    
    if not artifact_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Determine media type
    media_types = {
        ".mp4": "video/mp4",
        ".csv": "text/csv",
        ".json": "application/json",
        ".yaml": "text/yaml",
    }
    
    media_type = media_types.get(artifact_path.suffix, "application/octet-stream")
    
    return FileResponse(
        path=str(artifact_path),
        media_type=media_type,
        filename=filename
    )


@router.get("/mvp/test-phase-detection/{run_id}")
async def test_phase_detection(run_id: str):
    """
    Debug endpoint to verify motion-based phase detection is working on a given run.
    Reads pose_keypoints.json from outputs/{run_id} and runs PhaseDetector.
    """
    try:
        pose_json_path = Path(f"outputs/{run_id}/pose_keypoints.json")
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
    except Exception as e:
        return {
            "success": False,
            "run_id": run_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
