from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import BackgroundTasks
from typing import Optional
import tempfile
import shutil
from pathlib import Path

from ..utils.schemas import AnalyzeRequest, AnalyzeResponse
from ..utils.id_gen import generate_job_id
from ..storage.local_cache import job_store
from ..storage.db import record_video, record_metrics, record_feedback
from ..processing.pipeline import VideoProcessingPipeline


router = APIRouter(prefix="", tags=["analyze"])


def _process_job(
	job_id: str,
	video_path: Optional[str] = None,
	video_url: Optional[str] = None,
	user_id: Optional[str] = None,
	video_id: Optional[str] = None,
	camera_angle: Optional[str] = None,
	device_info: Optional[dict] = None,
) -> None:
	"""
	Process video job through complete pipeline.
	
	Args:
		job_id: Processing job ID
		video_path: Local video file path
		video_url: Video URL (if video_path not provided)
		user_id: User ID for database storage
		video_id: Existing video ID
		camera_angle: Camera angle type
		device_info: Device metadata
	"""
	try:
		# Update job status
		job_store[job_id] = {"status": "processing"}

		# Initialize pipeline
		pipeline = VideoProcessingPipeline(
			use_3d_lifting=False,  # Can be enabled when GPU available
			enable_ball_tracking=True,
		)

		# Process video
		if video_path:
			result = pipeline.process_video(
				video_path=video_path,
				user_id=user_id,
				video_id=video_id,
				camera_angle=camera_angle,
				device_info=device_info,
			)
		elif video_url:
			result = pipeline.process_video_from_url(
				video_url=video_url,
				user_id=user_id,
				video_id=video_id,
				camera_angle=camera_angle,
				device_info=device_info,
			)
		else:
			raise ValueError("Either video_path or video_url must be provided")

		# Clean up pipeline
		pipeline.cleanup()

		# Update job store with results
		annotated_video_path = result.get("annotated_video_path")
		annotated_video_url = None
		
		# Convert local path to URL if available
		if annotated_video_path:
			# For now, use file:// URL (can be enhanced to serve via HTTP)
			annotated_video_url = f"file://{annotated_video_path}"
		
		job_store[job_id] = {
			"status": "completed",
			"metrics": result.get("metrics", []),
			"feedback": result.get("feedback", []),
			"phases": result.get("phases", []),
			"video_id": result.get("video_id"),
			"pose_results": result.get("pose_results", 0),
			"hand_results": result.get("hand_results", 0),
			"ball_trajectory_length": result.get("ball_trajectory_length", 0),
			"annotated_video_url": annotated_video_url,
		}

	except Exception as e:
		# Mark job as failed
		job_store[job_id] = {
			"status": "failed",
			"error": str(e),
			"metrics": [],
			"feedback": [],
		}
		print(f"Job {job_id} processing failed: {e}")


@router.post("/analyze")
async def analyze(
	background_tasks: BackgroundTasks,
	file: Optional[UploadFile] = File(default=None),
	user_id: Optional[str] = None,
	angle: Optional[str] = None,
	fps: Optional[int] = None,
	device: Optional[str] = None,
	file_url: Optional[str] = None,
):
	"""
	Analyze basketball shooting video.
	
	Accepts either:
	- File upload (multipart/form-data)
	- JSON with file_url (from Supabase Storage)
	
	Returns job_id for polling results.
	"""
	job_id = generate_job_id()
	
	# Handle file upload (multipart/form-data)
	if file:
		# Save uploaded file temporarily
		suffix = Path(file.filename).suffix if file.filename else ".mp4"
		with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
			shutil.copyfileobj(file.file, tmp_file)
			video_path = tmp_file.name
		
		# Store video metadata in database if user_id provided
		video_id = None
		if user_id:
			try:
				video_id = record_video(
					user_id=user_id,
					file_url=file_url or f"uploaded_{job_id}{suffix}",
					angle=angle,
					fps=fps,
					device=device,
				)
			except Exception as e:
				print(f"Video metadata storage failed: {e}")
		
		# Queue processing job
		job_store[job_id] = {"status": "queued"}
		background_tasks.add_task(
			_process_job,
			job_id,
			video_path=video_path,
			user_id=user_id,
			video_id=video_id,
			camera_angle=angle,
			device_info={"device": device, "fps": fps} if device or fps else None,
		)
		return AnalyzeResponse(job_id=job_id, status="queued")
	
	# Handle JSON request with file_url (from Supabase Storage)
	if not user_id or not file_url:
		raise HTTPException(
			status_code=400,
			detail="Provide user_id and file_url for JSON requests"
		)
	
	job_id = generate_job_id()
	job_store[job_id] = {"status": "queued"}

	# Store video metadata in database
	try:
		video_id = record_video(
			user_id=user_id,
			file_url=file_url,
			angle=angle,
			fps=fps,
			device=device,
		)
	except Exception as e:
		print(f"Supabase video storage failed: {e}")
		video_id = None

	# Queue processing job
	background_tasks.add_task(
		_process_job,
		job_id,
		video_url=file_url,
		user_id=user_id,
		video_id=video_id,
		camera_angle=angle,
		device_info={"device": device, "fps": fps} if device or fps else None,
	)
	
	return AnalyzeResponse(job_id=job_id, status="queued")


