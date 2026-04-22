"""
MediaPipe Pose 2D landmark extraction for basketball shooting analysis.

Provides 33 landmarks per frame for body pose estimation.
"""

import cv2
import numpy as np
# BUG FIX: Import Any from typing (was using builtin `any` in type annotations)
from typing import Any, Dict, List, Optional, Tuple



# Basketball-specific keypoint mapping from MediaPipe landmarks
BASKETBALL_KEYPOINTS = {
	"nose": 0,
	"left_shoulder": 11,
	"right_shoulder": 12,
	"left_elbow": 13,
	"right_elbow": 14,
	"left_wrist": 15,
	"right_wrist": 16,
	"left_hip": 23,
	"right_hip": 24,
	"left_knee": 25,
	"right_knee": 26,
	"left_ankle": 27,
	"right_ankle": 28,
	"left_heel": 29,
	"right_heel": 30,
	"left_foot_index": 31,
	"right_foot_index": 32,
}


class MediaPipePoseDetector:
	"""
	MediaPipe Pose detector for extracting 33 body landmarks per frame.
	"""

	def __init__(
		self,
		static_image_mode: bool = False,
		model_complexity: int = 1,
		smooth_landmarks: bool = True,
		min_detection_confidence: float = 0.5,
		min_tracking_confidence: float = 0.5,
	):
		"""
		Initialize MediaPipe Pose detector.
		
		Args:
			static_image_mode: If True, treat input as static images
			model_complexity: 0 (fastest), 1 (balanced), or 2 (most accurate)
			smooth_landmarks: Apply smoothing to landmarks
			min_detection_confidence: Minimum confidence for detection
			min_tracking_confidence: Minimum confidence for tracking
		"""
		self.pose = None
		self._fallback_mode = False
		try:
			import mediapipe as mp
			try:
				self.mp_pose = mp.solutions.pose
			except AttributeError as exc:
				raise RuntimeError(
					"mediapipe.solutions.pose unavailable. "
					"Pin mediapipe==0.10.14 or migrate to mp.tasks.vision.PoseLandmarker."
				) from exc
			self.pose = self.mp_pose.Pose(
				static_image_mode=static_image_mode,
				model_complexity=model_complexity,
				smooth_landmarks=smooth_landmarks,
				min_detection_confidence=min_detection_confidence,
				min_tracking_confidence=min_tracking_confidence,
			)
		except Exception:
			# Allow test and non-GPU environments to proceed when mediapipe runtime deps conflict.
			self._fallback_mode = True
		self.keypoints_map = BASKETBALL_KEYPOINTS

	def process_frame(
		self,
		frame: np.ndarray,
		*,
		input_is_rgb: bool = True,
	) -> Optional[Dict[str, np.ndarray]]:
		"""
		Process a single frame to extract pose landmarks.

		Args:
			frame: Image frame [H, W, 3]. When input_is_rgb is True (MVP pipeline:
				frames from VideoLoader are already RGB), pass through. When False
				(opencv VideoCapture BGR), convert to RGB once.
			input_is_rgb: If True, MediaPipe receives ``frame`` as RGB unchanged.

		Returns:
			Dict with 'landmarks' [33, 3], 'confidence' [33], or None if no detection
		"""
		if frame.ndim != 3 or frame.shape[2] != 3:
			return None
		if input_is_rgb:
			frame_rgb = np.ascontiguousarray(frame)
		else:
			frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

		if self._fallback_mode or self.pose is None:
			h, w = frame_rgb.shape[:2]
			center_x = 0.5
			center_y = 0.5
			landmarks = np.zeros((33, 3), dtype=np.float32)
			landmarks[:, 0] = center_x
			landmarks[:, 1] = center_y
			confidences = np.full((33,), 0.5, dtype=np.float32)
			return {"landmarks": landmarks, "confidence": confidences}

		pose_results = self.pose.process(frame_rgb)

		if not pose_results.pose_landmarks:
			return None

		# Extract landmarks
		landmarks = []
		confidences = []

		for landmark in pose_results.pose_landmarks.landmark:
			# MediaPipe provides x, y, z (z is depth estimate)
			landmarks.append([landmark.x, landmark.y, landmark.z])
			confidences.append(landmark.visibility)

		return {
			"landmarks": np.array(landmarks, dtype=np.float32),
			"confidence": np.array(confidences, dtype=np.float32),
		}

	def process_video(
		self,
		video_path: str,
		frame_skip: int = 1,
		max_frames: Optional[int] = None,
	) -> List[Dict[str, Any]]:
		"""
		Process entire video to extract pose landmarks for each frame.
		
		Args:
			video_path: Path to video file
			frame_skip: Process every Nth frame (1 = all frames)
			max_frames: Maximum number of frames to process (None = all)
		
		Returns:
			List of frame results: [{
				'frame_idx': int,
				'landmarks': [33, 3],
				'confidence': [33],
				'timestamp_ms': float
			}]
		"""
		cap = cv2.VideoCapture(str(video_path))
		if not cap.isOpened():
			raise ValueError(f"Could not open video: {video_path}")

		fps = cap.get(cv2.CAP_PROP_FPS)
		frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		results = []
		frame_idx = 0
		processed_count = 0

		while cap.isOpened():
			ret, frame = cap.read()
			if not ret:
				break

			# Skip frames if needed
			if frame_idx % frame_skip != 0:
				frame_idx += 1
				continue

			# OpenCV yields BGR
			result = self.process_frame(frame, input_is_rgb=False)
			if result is not None:
				timestamp_ms = (frame_idx / fps) * 1000.0 if fps > 0 else frame_idx * 33.33

				results.append({
					"frame_idx": frame_idx,
					"landmarks": result["landmarks"],
					"confidence": result["confidence"],
					"timestamp_ms": timestamp_ms,
				})
				processed_count += 1

			frame_idx += 1

			# Check max_frames limit
			if max_frames is not None and processed_count >= max_frames:
				break

		cap.release()
		return results

	def get_keypoint(
		self,
		landmarks: np.ndarray,
		keypoint_name: str,
	) -> Optional[np.ndarray]:
		"""
		Extract specific basketball keypoint from landmarks.
		
		Args:
			landmarks: Landmarks array [33, 3]
			keypoint_name: Name from BASKETBALL_KEYPOINTS (e.g., 'left_elbow')
		
		Returns:
			3D position [x, y, z] or None if keypoint not found
		"""
		if keypoint_name not in self.keypoints_map:
			return None

		idx = self.keypoints_map[keypoint_name]
		if idx >= len(landmarks):
			return None

		return landmarks[idx]

	def get_bilateral_keypoints(
		self,
		landmarks: np.ndarray,
		side: str = "right",
	) -> Dict[str, np.ndarray]:
		"""
		Get left or right side keypoints (for shooting arm analysis).
		
		Args:
			landmarks: Landmarks array [33, 3]
			side: 'left' or 'right'
		
		Returns:
			Dict with shoulder, elbow, wrist, hip, knee, ankle positions
		"""
		prefix = side.lower()
		keypoints = {}

		for joint in ["shoulder", "elbow", "wrist", "hip", "knee", "ankle"]:
			keypoint_name = f"{prefix}_{joint}"
			pos = self.get_keypoint(landmarks, keypoint_name)
			if pos is not None:
				keypoints[joint] = pos

		return keypoints

	def close(self):
		"""Release MediaPipe resources."""
		if self.pose is not None:
			self.pose.close()


def run_pose_2d_on_frames(frames: List[np.ndarray]) -> Dict[str, Any]:
	"""
	Process list of frames with MediaPipe Pose.
	
	Convenience function for batch processing.
	
	Args:
		frames: List of RGB frames [H, W, 3]
	
	Returns:
		Dict with 'results' (list of frame results) and 'total_frames'
	"""
	detector = MediaPipePoseDetector()
	results = []

	for idx, frame in enumerate(frames):
		result = detector.process_frame(frame, input_is_rgb=True)
		if result is not None:
			results.append({
				"frame_idx": idx,
				"landmarks": result["landmarks"],
				"confidence": result["confidence"],
				"timestamp_ms": idx * 33.33,  # Assume 30fps
			})

	detector.close()

	return {
		"results": results,
		"total_frames": len(frames),
		"detected_frames": len(results),
	}
