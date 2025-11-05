"""
MediaPipe Hands 2D landmark extraction for grip quality analysis.

Provides 21 landmarks per hand for finger spread and palm contact detection.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Optional, Tuple


# MediaPipe Hands landmark indices
HAND_LANDMARK_INDICES = {
	"wrist": 0,
	"thumb_cmc": 1,
	"thumb_mcp": 2,
	"thumb_ip": 3,
	"thumb_tip": 4,
	"index_mcp": 5,
	"index_pip": 6,
	"index_dip": 7,
	"index_tip": 8,
	"middle_mcp": 9,
	"middle_pip": 10,
	"middle_dip": 11,
	"middle_tip": 12,
	"ring_mcp": 13,
	"ring_pip": 14,
	"ring_dip": 15,
	"ring_tip": 16,
	"pinky_mcp": 17,
	"pinky_pip": 18,
	"pinky_dip": 19,
	"pinky_tip": 20,
}


class MediaPipeHandsDetector:
	"""
	MediaPipe Hands detector for extracting 21 landmarks per hand.
	"""

	def __init__(
		self,
		static_image_mode: bool = False,
		max_num_hands: int = 2,
		min_detection_confidence: float = 0.5,
		min_tracking_confidence: float = 0.5,
	):
		"""
		Initialize MediaPipe Hands detector.
		
		Args:
			static_image_mode: If True, treat input as static images
			max_num_hands: Maximum number of hands to detect (1 or 2)
			min_detection_confidence: Minimum confidence for detection
			min_tracking_confidence: Minimum confidence for tracking
		"""
		self.mp_hands = mp.solutions.hands
		self.hands = self.mp_hands.Hands(
			static_image_mode=static_image_mode,
			max_num_hands=max_num_hands,
			min_detection_confidence=min_detection_confidence,
			min_tracking_confidence=min_tracking_confidence,
		)

	def process_frame(self, frame: np.ndarray) -> List[Dict[str, any]]:
		"""
		Process a single frame to extract hand landmarks.
		
		Args:
			frame: RGB image frame [H, W, 3]
		
		Returns:
			List of hand results: [{
				'handedness': 'Left' or 'Right',
				'landmarks': [21, 3],
				'confidence': float,
				'world_landmarks': [21, 3] (optional)
			}]
		"""
		# MediaPipe expects RGB
		if frame.shape[2] == 3:
			frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		else:
			frame_rgb = frame

		hands_results = self.hands.process(frame_rgb)
		results = []

		if not hands_results.multi_hand_landmarks:
			return results

		for hand_idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
			# Get handedness (Left or Right)
			handedness = "Right"  # Default
			if hands_results.multi_handedness:
				handedness_info = hands_results.multi_handedness[hand_idx]
				handedness = handedness_info.classification[0].label

			# Extract normalized landmarks (x, y, z in [0, 1])
			landmarks = []
			for landmark in hand_landmarks.landmark:
				landmarks.append([landmark.x, landmark.y, landmark.z])

			# Get world landmarks if available (3D coordinates in meters)
			world_landmarks = None
			if hands_results.multi_hand_world_landmarks:
				world_landmarks_list = []
				for landmark in hands_results.multi_hand_world_landmarks[hand_idx].landmark:
					world_landmarks_list.append([landmark.x, landmark.y, landmark.z])
				world_landmarks = np.array(world_landmarks_list, dtype=np.float32)

			# Get confidence from handedness
			confidence = 1.0
			if hands_results.multi_handedness:
				confidence = hands_results.multi_handedness[hand_idx].classification[0].score

			results.append({
				"handedness": handedness,
				"landmarks": np.array(landmarks, dtype=np.float32),
				"world_landmarks": world_landmarks,
				"confidence": float(confidence),
			})

		return results

	def process_video(
		self,
		video_path: str,
		frame_skip: int = 1,
		max_frames: Optional[int] = None,
	) -> List[Dict[str, any]]:
		"""
		Process entire video to extract hand landmarks for each frame.
		
		Args:
			video_path: Path to video file
			frame_skip: Process every Nth frame (1 = all frames)
			max_frames: Maximum number of frames to process (None = all)
		
		Returns:
			List of frame results: [{
				'frame_idx': int,
				'hands': [hand_results],
				'timestamp_ms': float
			}]
		"""
		cap = cv2.VideoCapture(str(video_path))
		if not cap.isOpened():
			raise ValueError(f"Could not open video: {video_path}")

		fps = cap.get(cv2.CAP_PROP_FPS)
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

			# Process frame
			hand_results = self.process_frame(frame)
			if hand_results:
				timestamp_ms = (frame_idx / fps) * 1000.0 if fps > 0 else frame_idx * 33.33

				results.append({
					"frame_idx": frame_idx,
					"hands": hand_results,
					"timestamp_ms": timestamp_ms,
				})
				processed_count += 1

			frame_idx += 1

			# Check max_frames limit
			if max_frames is not None and processed_count >= max_frames:
				break

		cap.release()
		return results

	def get_landmark(self, landmarks: np.ndarray, landmark_name: str) -> Optional[np.ndarray]:
		"""
		Extract specific hand landmark by name.
		
		Args:
			landmarks: Hand landmarks array [21, 3]
			landmark_name: Name from HAND_LANDMARK_INDICES (e.g., 'thumb_tip')
		
		Returns:
			3D position [x, y, z] or None if not found
		"""
		if landmark_name not in HAND_LANDMARK_INDICES:
			return None

		idx = HAND_LANDMARK_INDICES[landmark_name]
		if idx >= len(landmarks):
			return None

		return landmarks[idx]

	def detect_grip_quality(
		self,
		hand_landmarks: np.ndarray,
		ball_center: Optional[np.ndarray] = None,
	) -> Dict[str, float]:
		"""
		Detect grip quality based on finger spread and palm contact.
		
		Args:
			hand_landmarks: Hand landmarks array [21, 3]
			ball_center: Optional 3D ball center position
		
		Returns:
			Dict with grip_quality_score, thumb_index_distance, and confidence
		"""
		from ..metrics.grip import compute_grip_quality

		return compute_grip_quality(hand_landmarks, ball_center)

	def associate_with_wrist(
		self,
		hand_results: List[Dict[str, any]],
		wrist_3d: np.ndarray,
		threshold: float = 0.1,
	) -> Optional[Dict[str, any]]:
		"""
		Associate hand detection with pose wrist position.
		
		Finds the hand closest to the given wrist position.
		
		Args:
			hand_results: List of hand detection results
			wrist_3d: 3D wrist position from pose detection
			threshold: Maximum distance threshold for association
		
		Returns:
			Matching hand result or None
		"""
		if not hand_results:
			return None

		best_match = None
		best_distance = float("inf")

		for hand_result in hand_results:
			# Get wrist landmark from hand
			wrist_landmark = self.get_landmark(hand_result["landmarks"], "wrist")
			if wrist_landmark is None:
				continue

			# Use world landmarks if available, otherwise normalized
			if hand_result.get("world_landmarks") is not None:
				hand_wrist = self.get_landmark(hand_result["world_landmarks"], "wrist")
			else:
				hand_wrist = wrist_landmark

			if hand_wrist is None:
				continue

			# Compute distance
			distance = np.linalg.norm(hand_wrist - wrist_3d)
			if distance < best_distance:
				best_distance = distance
				best_match = hand_result

		# Return if within threshold
		if best_match is not None and best_distance <= threshold:
			return best_match

		return None

	def close(self):
		"""Release MediaPipe resources."""
		self.hands.close()


def detect_grip_quality(hand_landmarks: np.ndarray) -> Dict[str, float]:
	"""
	Convenience function to detect grip quality from hand landmarks.
	
	Args:
		hand_landmarks: Hand landmarks array [21, 3]
	
	Returns:
		Dict with grip metrics
	"""
	from ..metrics.grip import compute_grip_quality

	return compute_grip_quality(hand_landmarks, None)
