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

from ..mvp.core.pipeline import MVPPipeline
from ..utils.id_gen import generate_job_id

router = APIRouter(prefix="/mvp", tags=["mvp"])

# In-memory job store (use Redis in production)
job_store: Dict[str, Dict[str, Any]] = {}


def _process_video_job(
    job_id: str,
    video_path: str,
    shooting_side: str = "auto"
):
    """Background task to process video."""
    try:
        # Update status
        job_store[job_id]["status"] = "processing"
        
        # Run pipeline
        pipeline = MVPPipeline()
        result = pipeline.process_video(video_path, shooting_side)
        
        # Load angles data for React Native
        angles_csv = Path(result["output_dir"]) / "angles.csv"
        angles_df = pd.read_csv(angles_csv)
        
        angles_data = {
            "frames": angles_df["frame_id"].tolist(),
            "timestamps": angles_df["timestamp"].tolist(),
            "elbow": angles_df["elbow_angle"].tolist(),
            "knee": angles_df["knee_angle"].tolist(),
            "wrist": angles_df["wrist_angle"].tolist(),
        }
        
        # Update job store with results
        job_store[job_id] = {
            "status": "completed",
            "run_id": result["run_id"],
            "metrics": result["metrics"],
            "overall_score": result["overall_score"],
            "feedback_summary": result["feedback_summary"],
            "shot_window": result["shot_window"],
            "shooting_side": result["shooting_side"],
            "angles_data": angles_data,
            "artifacts": {
                "overlay_video": f"/mvp/artifacts/{result['run_id']}/overlay.mp4",
                "angles_csv": f"/mvp/artifacts/{result['run_id']}/angles.csv",
                "report_json": f"/mvp/artifacts/{result['run_id']}/report.json",
            },
            "quality_warnings": result.get("quality_warnings", []),
        }
        
    except Exception as e:
        job_store[job_id] = {
            "status": "failed",
            "error": str(e),
        }
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
    # Generate job ID
    job_id = generate_job_id()
    
    # Save uploaded file temporarily
    suffix = Path(file.filename).suffix if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        video_path = tmp_file.name
    
    # Queue processing job
    job_store[job_id] = {"status": "queued"}
    background_tasks.add_task(
        _process_video_job,
        job_id,
        video_path,
        shooting_side
    )
    
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
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_store[job_id]


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
