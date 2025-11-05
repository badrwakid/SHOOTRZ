"""
Main video processing pipeline for basketball shooting analysis.

Orchestrates: load frames → 2D pose → ball tracking → phase detection → 
3D lifting (optional) → metrics → feedback → database storage.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import tempfile
import shutil

from ..inference.pose_2d import MediaPipePoseDetector
from ..inference.hands_2d import MediaPipeHandsDetector
from ..inference.ball_tracker import detect_and_track_ball
from ..inference.phase_detector import PhaseDetector
from ..inference.lift_3d import lift_3d_pose
from ..metrics.calculator import MetricsCalculator
from ..feedback.engine import generate_feedback
from ..storage.db import record_video, record_metrics, record_feedback
from ..utils.error_handler import retry, handle_processing_error, validate_video_file
from ..utils.performance import timeit


class VideoProcessingPipeline:
	"""
	Orchestrates complete video processing pipeline.
	"""

	def __init__(
		self,
		use_3d_lifting: bool = False,
		enable_ball_tracking: bool = True,
	):
		"""
		Initialize processing pipeline.
		
		Args:
			use_3d_lifting: Whether to use 3D pose lifting (requires GPU)
			enable_ball_tracking: Whether to track ball trajectory
		"""
		self.pose_detector = MediaPipePoseDetector()
		self.hands_detector = MediaPipeHandsDetector()
		self.phase_detector = PhaseDetector()
		self.metrics_calculator = MetricsCalculator(use_3d=use_3d_lifting)
		self.use_3d_lifting = use_3d_lifting
		self.enable_ball_tracking = enable_ball_tracking

	@timeit
	def load_video_frames(
		self,
		video_path: str,
		max_frames: Optional[int] = None,
		frame_skip: int = 1,
	) -> tuple[List[np.ndarray], float]:
		"""
		Load frames from video file.
		
		Args:
			video_path: Path to video file
			max_frames: Maximum frames to load (None = all)
			frame_skip: Load every Nth frame (1 = all frames)
		
		Returns:
			Tuple of (frames list, fps)
		"""
		# Validate video file first
		is_valid, error_msg = validate_video_file(video_path)
		if not is_valid:
			raise ValueError(f"Invalid video file: {error_msg}")

		cap = cv2.VideoCapture(str(video_path))
		if not cap.isOpened():
			raise ValueError(f"Could not open video: {video_path}")

		fps = cap.get(cv2.CAP_PROP_FPS)
		frames = []
		frame_idx = 0

		while cap.isOpened():
			ret, frame = cap.read()
			if not ret:
				break

			if frame_idx % frame_skip == 0:
				# Convert BGR to RGB
				frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				frames.append(frame_rgb)

			frame_idx += 1

			if max_frames is not None and len(frames) >= max_frames:
				break

		cap.release()
		
		if not frames:
			raise ValueError("No frames extracted from video")

		return frames, fps

	@retry(max_attempts=2, delay=1.0)
	@timeit
	def process_video(
		self,
		video_path: str,
		user_id: Optional[str] = None,
		video_id: Optional[str] = None,
		camera_angle: Optional[str] = None,
		device_info: Optional[Dict] = None,
	) -> Dict[str, Any]:
		"""
		Process video through complete pipeline.
		
		Args:
			video_path: Path to video file
			user_id: User ID for database storage
			video_id: Optional existing video ID
			camera_angle: Camera angle type
			device_info: Device metadata
		
		Returns:
			Dict with processing results: {
				'video_id': str,
				'metrics': List[Dict],
				'feedback': List[Dict],
				'phases': List[Dict],
				'status': str
			}
		"""
		# Step 1: Load video frames
		frames, fps = self.load_video_frames(video_path)

		# Step 2: Run 2D pose detection
		pose_results = []
		for idx, frame in enumerate(frames):
			try:
				result = self.pose_detector.process_frame(frame)
				if result:
					pose_results.append({
						"frame_idx": idx,
						"landmarks": result["landmarks"],
						"confidence": result["confidence"],
						"timestamp_ms": (idx / fps) * 1000.0 if fps > 0 else idx * 33.33,
					})
			except Exception as e:
				handle_processing_error(e, context=f"Pose detection frame {idx}", return_default=None)

		if not pose_results:
			raise ValueError("No pose detections found in video")

		# Step 3: Run hand detection
		hand_results = []
		for idx, frame in enumerate(frames):
			try:
				hands = self.hands_detector.process_frame(frame)
				if hands:
					hand_results.append({
						"frame_idx": idx,
						"hands": hands,
						"timestamp_ms": (idx / fps) * 1000.0 if fps > 0 else idx * 33.33,
					})
			except Exception as e:
				handle_processing_error(e, context=f"Hand detection frame {idx}", return_default=None)

		# Step 4: Ball tracking (if enabled)
		ball_trajectory = None
		ball_timestamps = None
		if self.enable_ball_tracking:
			try:
				ball_result = detect_and_track_ball(frames)
				if ball_result and "trajectory" in ball_result:
					ball_trajectory = ball_result["trajectory"]
					# Extract positions from trajectory
					if ball_trajectory:
						positions = [
							np.array(t["center"] + [t.get("z", 0.0)]) if isinstance(t, dict) else t
							for t in ball_trajectory
							if t is not None
						]
						ball_trajectory = positions if positions else None
						if ball_trajectory:
							ball_timestamps = [
								(i / fps) if fps > 0 else i * 0.033
								for i in range(len(ball_trajectory))
							]
			except Exception as e:
				print(f"Ball tracking failed: {e}")
				ball_trajectory = None

		# Step 5: Detect phases
		phases = self.phase_detector.detect_phases(
			pose_results,
			ball_trajectory,
			ball_timestamps,
		)

		# Step 6: Optional 3D lifting
		pose_3d = None
		if self.use_3d_lifting and pose_results:
			try:
				# Extract 2D landmarks series
				pose_2d_series = [r["landmarks"] for r in pose_results]
				lift_result = lift_3d_pose(pose_2d_series, method="posemagic")
				if lift_result and "keypoints_3d" in lift_result:
					pose_3d = lift_result["keypoints_3d"]
			except Exception as e:
				print(f"3D lifting failed: {e}")
				pose_3d = None

		# Step 7: Compute metrics
		try:
			metrics = self.metrics_calculator.compute_all_metrics(
				pose_results=pose_results,
				hand_results=hand_results,
				ball_trajectory=ball_trajectory,
				pose_3d=pose_3d,
				shot_distance=None,  # Will be computed from ball trajectory if available
				rim_position=None,  # Can be enhanced with hoop detection
			)
		except Exception as e:
			print(f"Metrics computation failed: {e}")
			metrics = []

		# Step 8: Generate feedback
		try:
			feedback = generate_feedback(metrics)
		except Exception as e:
			print(f"Feedback generation failed: {e}")
			feedback = []

		# Step 9: Store results in database (if user_id provided)
		if user_id and video_id:
			try:
				# Store metrics with enhanced data
				metric_records = [
					{
						"metric_name": m["metric_name"],
						"value": m["value"],
						"unit": m.get("unit"),
						"confidence": m.get("confidence", 0.0),
						"phase": m.get("phase"),
						"frame_idx": m.get("frame_idx"),
					}
					for m in metrics
				]
				metric_ids = record_metrics(video_id, metric_records)

				# Store feedback (link to metrics)
				if metric_ids and feedback:
					feedback_records = []
					for fb, metric_id in zip(feedback[:len(metric_ids)], metric_ids):
						feedback_records.append({
							"metric_id": metric_id,
							"message": fb.get("message", ""),
							"severity": fb.get("severity", "info"),
						})
					if feedback_records:
						record_feedback(feedback_records)
			except Exception as e:
				print(f"Database storage failed: {e}")

		return {
			"video_id": video_id,
			"metrics": metrics,
			"feedback": feedback,
			"phases": [
				{
					"phase": p["phase"].value if hasattr(p["phase"], "value") else str(p["phase"]),
					"start_frame": p["start_frame"],
					"end_frame": p["end_frame"],
					"confidence": p.get("confidence", 0.0),
				}
				for p in phases
			],
			"pose_results": len(pose_results),
			"hand_results": len(hand_results),
			"ball_trajectory_length": len(ball_trajectory) if ball_trajectory else 0,
			"status": "completed",
		}

	@retry(max_attempts=2, delay=1.0)
	def process_video_from_url(
		self,
		video_url: str,
		user_id: Optional[str] = None,
		video_id: Optional[str] = None,
		**kwargs,
	) -> Dict[str, Any]:
		"""
		Process video from URL (downloads temporarily).
		
		Args:
			video_url: URL to video file
			user_id: User ID for database storage
			video_id: Optional existing video ID
			**kwargs: Additional arguments for process_video
		
		Returns:
			Processing results dict
		"""
		import requests
		import tempfile

		# Download video to temporary file
		response = requests.get(video_url, stream=True, timeout=30)
		response.raise_for_status()

		with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
			shutil.copyfileobj(response.raw, tmp_file)
			tmp_path = tmp_file.name

		try:
			result = self.process_video(tmp_path, user_id, video_id, **kwargs)
		finally:
			# Clean up temporary file
			Path(tmp_path).unlink(missing_ok=True)

		return result

	def cleanup(self):
		"""Release resources."""
		try:
			self.pose_detector.close()
			self.hands_detector.close()
		except Exception as e:
			print(f"Error during cleanup: {e}")
