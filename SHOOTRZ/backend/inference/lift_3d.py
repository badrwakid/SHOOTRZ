"""
3D pose lifting from 2D landmarks.

Supports PoseMagic (causal) and HybrIK-Transformer as fallback.
Includes temporal smoothing and missing frame handling.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from scipy.signal import savgol_filter

from ..metrics.biomechanics import smooth_3d_positions
from ..utils.error_handler import retry, handle_processing_error


def normalize_landmarks(landmarks_2d: np.ndarray) -> np.ndarray:
	"""
	Normalize 2D landmarks for 3D lifting.
	
	Subtracts pelvis center and scales by shoulder width.
	MediaPipe landmarks: pelvis center is average of left_hip (23) and right_hip (24)
	"""
	if len(landmarks_2d) < 33:
		return landmarks_2d

	# Pelvis center (average of hips)
	left_hip = landmarks_2d[23, :2] if landmarks_2d.shape[1] >= 2 else landmarks_2d[23]
	right_hip = landmarks_2d[24, :2] if landmarks_2d.shape[1] >= 2 else landmarks_2d[24]
	pelvis_center = (left_hip + right_hip) / 2.0

	# Shoulder width for scaling
	left_shoulder = landmarks_2d[11, :2] if landmarks_2d.shape[1] >= 2 else landmarks_2d[11]
	right_shoulder = landmarks_2d[12, :2] if landmarks_2d.shape[1] >= 2 else landmarks_2d[12]
	shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)

	if shoulder_width == 0:
		shoulder_width = 1.0  # Avoid division by zero

	# Normalize: subtract pelvis, scale by shoulder width
	normalized = landmarks_2d.copy()
	if normalized.shape[1] >= 2:
		normalized[:, :2] = (normalized[:, :2] - pelvis_center) / shoulder_width

	return normalized


def interpolate_missing_frames(
	landmarks_series: List[np.ndarray],
) -> List[np.ndarray]:
	"""
	Interpolate missing frames in landmark series.
	
	Uses linear interpolation between existing frames.
	"""
	if not landmarks_series:
		return []

	# Find frames with valid landmarks (not all zeros/NaN)
	valid_indices = []
	for i, lm in enumerate(landmarks_series):
		if lm is not None and len(lm) > 0:
			if not np.all(np.isnan(lm)) and not np.all(lm == 0):
				valid_indices.append(i)

	if len(valid_indices) < 2:
		# Not enough data for interpolation
		return landmarks_series

	# Interpolate missing frames
	interpolated = landmarks_series.copy()
	for i in range(len(interpolated)):
		if i not in valid_indices:
			# Find nearest valid frames
			prev_idx = max([v for v in valid_indices if v < i], default=None)
			next_idx = min([v for v in valid_indices if v > i], default=None)

			if prev_idx is not None and next_idx is not None:
				# Linear interpolation
				alpha = (i - prev_idx) / (next_idx - prev_idx)
				interpolated[i] = (
					(1 - alpha) * interpolated[prev_idx] + alpha * interpolated[next_idx]
				)
			elif prev_idx is not None:
				interpolated[i] = interpolated[prev_idx]
			elif next_idx is not None:
				interpolated[i] = interpolated[next_idx]

	return interpolated


@retry(max_attempts=2, delay=0.5, exceptions=(ValueError,))
def lift_3d_pose(
	pose_2d_series: List[np.ndarray],
	method: str = "posemagic",
	sequence_length: int = 81,
	enable_smoothing: bool = True,
) -> Dict[str, Any]:
	"""
	Lift 2D pose landmarks to 3D using specified method.
	
	Args:
		pose_2d_series: List of 2D landmark arrays [N frames, 33 landmarks, 2/3 coords]
		method: "posemagic" (causal) or "hybrik" (fallback)
		sequence_length: Window length for temporal model (PoseMagic)
		enable_smoothing: Whether to apply temporal smoothing
	
	Returns:
		Dict with 'keypoints_3d' [N, 17, 3], 'method', 'confidence'
	"""
	if not pose_2d_series:
		return {
			"keypoints_3d": [],
			"method": method,
			"confidence": 0.0,
			"error": "Empty pose series",
		}

	try:
		# Convert to numpy array
		if isinstance(pose_2d_series[0], list):
			pose_2d_array = np.array(pose_2d_series)
		else:
			pose_2d_array = np.array(pose_2d_series)

		if len(pose_2d_array.shape) != 3:
			raise ValueError(f"Expected 3D array [frames, landmarks, coords], got shape {pose_2d_array.shape}")

		num_frames = pose_2d_array.shape[0]

		# Interpolate missing frames
		pose_2d_list = [pose_2d_array[i] for i in range(num_frames)]
		pose_2d_list = interpolate_missing_frames(pose_2d_list)
		pose_2d_array = np.array(pose_2d_list)

		# Normalize landmarks
		normalized_series = []
		for frame_landmarks in pose_2d_array:
			normalized = normalize_landmarks(frame_landmarks)
			normalized_series.append(normalized)

		# Method-specific lifting
		if method == "posemagic":
			keypoints_3d = lift_3d_posemagic(normalized_series, sequence_length)
		elif method == "hybrik":
			keypoints_3d = lift_3d_hybrik(normalized_series)
		else:
			raise ValueError(f"Unknown method: {method}")

		# Temporal smoothing
		if enable_smoothing and len(keypoints_3d) > 0:
			keypoints_3d = smooth_3d_positions(
				np.array(keypoints_3d),
				window_length=11,
				polyorder=2,
			).tolist()

		# Calculate confidence based on number of valid frames
		confidence = min(1.0, len(keypoints_3d) / max(10, num_frames))

		return {
			"keypoints_3d": keypoints_3d,
			"method": method,
			"confidence": confidence,
		}

	except Exception as e:
		return handle_processing_error(
			e,
			context=f"3D lifting with method {method}",
			return_default={
				"keypoints_3d": [],
				"method": method,
				"confidence": 0.0,
				"error": str(e),
			},
		)


def lift_3d_posemagic(
	normalized_series: List[np.ndarray],
	sequence_length: int = 81,
) -> List[np.ndarray]:
	"""
	Lift 3D using PoseMagic causal variant.
	
	For MVP: Returns placeholder structure.
	In production: Load PoseMagic model and run inference.
	
	Note: Actual PoseMagic implementation requires model weights and PyTorch.
	"""
	# Placeholder implementation
	# In production, this would:
	# 1. Load PoseMagic causal model weights
	# 2. Process in sliding windows of sequence_length
	# 3. Convert normalized 2D to 3D joints [17 keypoints]
	
	num_frames = len(normalized_series)
	if num_frames == 0:
		return []

	# Placeholder: Return 3D keypoints with zero depth
	# This allows the system to work without PoseMagic model
	keypoints_3d = []
	for frame_lm in normalized_series:
		# Convert 33 MediaPipe landmarks to 17 SMPL keypoints
		# Simplified mapping for MVP
		smpl_keypoints = np.zeros((17, 3))
		
		# Map key MediaPipe points to SMPL
		if len(frame_lm) >= 33:
			# Head (nose)
			smpl_keypoints[0] = [frame_lm[0, 0], frame_lm[0, 1], 0.0]
			# Shoulders
			smpl_keypoints[1] = [frame_lm[11, 0], frame_lm[11, 1], 0.0]  # Left
			smpl_keypoints[2] = [frame_lm[12, 0], frame_lm[12, 1], 0.0]  # Right
			# Elbows
			smpl_keypoints[3] = [frame_lm[13, 0], frame_lm[13, 1], 0.0]  # Left
			smpl_keypoints[4] = [frame_lm[14, 0], frame_lm[14, 1], 0.0]  # Right
			# Wrists
			smpl_keypoints[5] = [frame_lm[15, 0], frame_lm[15, 1], 0.0]  # Left
			smpl_keypoints[6] = [frame_lm[16, 0], frame_lm[16, 1], 0.0]  # Right
			# Hips
			smpl_keypoints[7] = [frame_lm[23, 0], frame_lm[23, 1], 0.0]  # Left
			smpl_keypoints[8] = [frame_lm[24, 0], frame_lm[24, 1], 0.0]  # Right
			# Knees
			smpl_keypoints[9] = [frame_lm[25, 0], frame_lm[25, 1], 0.0]  # Left
			smpl_keypoints[10] = [frame_lm[26, 0], frame_lm[26, 1], 0.0]  # Right
			# Ankles
			smpl_keypoints[11] = [frame_lm[27, 0], frame_lm[27, 1], 0.0]  # Left
			smpl_keypoints[12] = [frame_lm[28, 0], frame_lm[28, 1], 0.0]  # Right

		keypoints_3d.append(smpl_keypoints)

	return keypoints_3d


def lift_3d_hybrik(
	normalized_series: List[np.ndarray],
) -> List[np.ndarray]:
	"""
	Lift 3D using HybrIK-Transformer (per-frame fallback).
	
	For MVP: Returns placeholder structure.
	In production: Load HybrIK model and run per-frame inference.
	"""
	# Similar placeholder to PoseMagic
	# In production, this would run HybrIK-Transformer on each frame
	return lift_3d_posemagic(normalized_series, sequence_length=1)
