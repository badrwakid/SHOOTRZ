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
		pose_strategy: str = "mediapipe",
		generate_annotated: bool = False,
		enable_hands: bool = False,
	):
		self.pose_detector = MediaPipePoseDetector()
		self.hands_detector = MediaPipeHandsDetector() if enable_hands else None
		self.phase_detector = PhaseDetector()
		self.metrics_calculator = MetricsCalculator(use_3d=use_3d_lifting)
		self.use_3d_lifting = use_3d_lifting
		self.enable_ball_tracking = enable_ball_tracking
		self.generate_annotated = generate_annotated
		self.enable_hands = enable_hands
		self.pose_strategy = pose_strategy
		self.yolo_pose_detector = None
		if pose_strategy in ["yolo", "ensemble"]:
			try:
				from ..inference.yolo_pose_detector import YOLOv8PoseDetector
				self.yolo_pose_detector = YOLOv8PoseDetector(use_finetuned=True)
			except Exception as e:
				print(f"Warning: Could not initialize YOLOv8-pose: {e}")
				if pose_strategy == "yolo":
					self.pose_strategy = "mediapipe"

	def iter_video_frames(self, video_path: str):
		"""Validate video, return (fps, total_frames, frame_generator)."""
		is_valid, err = validate_video_file(video_path)
		if not is_valid:
			raise ValueError(f"Invalid video file: {err}")
		cap = cv2.VideoCapture(str(video_path))
		if not cap.isOpened():
			raise ValueError(f"Could not open video: {video_path}")
		fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
		total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
		if total <= 0 or fps <= 0:
			cap.release()
			raise ValueError("Video metadata unreadable (fps/total=0)")

		def _gen():
			try:
				i = 0
				while True:
					ok, frame = cap.read()
					if not ok:
						break
					yield i, frame
					i += 1
			finally:
				cap.release()

		return fps, total, _gen()

	@staticmethod
	def _empty_result(video_id, reason: str) -> dict:
		return {
			"video_id": video_id,
			"metrics": [],
			"feedback": [],
			"shot_score": {"score": None, "breakdown": [], "confidence": 0.0, "reason": reason},
			"phases": [],
			"annotated_video_path": None,
			"pose_results": 0,
			"hand_results": 0,
			"ball_trajectory_length": 0,
			"status": "completed_low_quality",
		}

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
		fps, total, frames_iter = self.iter_video_frames(video_path)

		# Target ~90 pose frames — enough for phase detection, cheap on CPU
		target = 90
		stride = max(1, total // target)

		pose_results = []
		ball_rgb_frames: List[np.ndarray] = []
		ball_rgb_indices: List[int] = []

		for idx, bgr in frames_iter:
			if idx % stride != 0:
				continue
			rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
			rgb.flags.writeable = False

			pose = self.pose_detector.process_frame(rgb)
			if pose is not None:
				pose_results.append({
					"frame_idx": idx,
					"landmarks": pose["landmarks"],
					"confidence": pose["confidence"],
					"timestamp_ms": (idx / fps) * 1000.0,
				})

			if len(ball_rgb_frames) < 60:
				ball_rgb_frames.append(rgb)
				ball_rgb_indices.append(idx)

			del bgr

		if not pose_results:
			return self._empty_result(video_id, "no_pose_detected")
		if len(pose_results) < 5:
			return self._empty_result(video_id, "insufficient_pose_frames")

		# Ball tracking (reuses already-decoded RGB — no second pass)
		ball_trajectory: Optional[List[np.ndarray]] = None
		ball_timestamps: Optional[List[float]] = None
		if self.enable_ball_tracking and ball_rgb_frames:
			try:
				bt = detect_and_track_ball(ball_rgb_frames)
				traj = bt.get("trajectory") if bt else None
				if traj:
					positions = [
						np.array(list(t["center"]) + [t.get("z", 0.0)])
						if isinstance(t, dict) else np.asarray(t)
						for t in traj if t is not None
					]
					if positions:
						ball_trajectory = positions
						ball_timestamps = [ball_rgb_indices[i] / fps for i in range(len(positions))]
			except Exception as e:
				print(f"Ball tracking failed: {e}")

		# Phase detection (single call here)
		phases = self.phase_detector.detect_phases(pose_results, ball_trajectory, ball_timestamps)

		# Metrics (hands disabled for MVP)
		try:
			metrics = self.metrics_calculator.compute_all_metrics(
				pose_results=pose_results,
				hand_results=None,
				ball_trajectory=ball_trajectory,
				pose_3d=None,
				shot_distance=None,
				rim_position=None,
			)
		except Exception as e:
			print(f"Metrics computation failed: {e}")
			metrics = []

		# SHOOTRZ score (0-100) — imported lazily so Day 1 works before angles.py is replaced
		try:
			from ..metrics.angles import compute_shot_score
			shot_score = compute_shot_score(metrics)
		except Exception as e:
			print(f"Score aggregation failed: {e}")
			shot_score = {"score": None, "breakdown": [], "confidence": 0.0}

		# Feedback
		try:
			feedback = generate_feedback(metrics)
		except Exception as e:
			print(f"Feedback generation failed: {e}")
			feedback = []

		# DB write (best-effort; errors don't fail the request)
		if user_id and video_id:
			try:
				metric_records = [
					{k: m.get(k) for k in ("metric_name", "value", "unit", "confidence", "phase", "frame_idx")}
					for m in metrics
				]
				metric_ids = record_metrics(video_id, metric_records)
				if metric_ids and feedback:
					fb_records = [
						{"metric_id": mid, "message": fb.get("message", ""), "severity": fb.get("severity", "info")}
						for fb, mid in zip(feedback, metric_ids)
					]
					if fb_records:
						record_feedback(fb_records)
			except Exception as e:
				print(f"DB storage failed: {e}")

		return {
			"video_id": video_id,
			"metrics": metrics,
			"feedback": feedback,
			"shot_score": shot_score,
			"phases": [
				{
					"phase": p["phase"].value if hasattr(p["phase"], "value") else str(p["phase"]),
					"start_frame": p["start_frame"],
					"end_frame": p["end_frame"],
					"confidence": p.get("confidence", 0.0),
				}
				for p in phases
			],
			"annotated_video_path": None,
			"pose_results": len(pose_results),
			"hand_results": 0,
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
			if self.hands_detector is not None:
				self.hands_detector.close()
		except Exception as e:
			print(f"Error during cleanup: {e}")
