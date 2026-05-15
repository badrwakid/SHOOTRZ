"""
Research-validated biomechanics calculations for basketball shooting analysis.

Based on:
- Cabarkapa et al. (2021): Free throw shooting mechanics
- Okazaki et al. (2012): Jump shot mechanics and release angles
"""

import numpy as np
from typing import Dict, Optional
from scipy.signal import savgol_filter


def joint_angle(
	point_a: np.ndarray,
	point_b: np.ndarray,
	point_c: np.ndarray,
) -> float:
	"""
	Compute internal angle at joint B formed by points A-B-C.
	
	Args:
		point_a: First point (e.g., shoulder)
		point_b: Joint point (e.g., elbow)
		point_c: Third point (e.g., wrist)
	
	Returns:
		Angle in degrees (0-180°)
	"""
	ba = point_a - point_b
	bc = point_c - point_b
	
	# Compute cosine of angle
	dot_product = np.dot(ba, bc)
	magnitudes = np.linalg.norm(ba) * np.linalg.norm(bc)
	
	if magnitudes == 0:
		return 0.0
	
	cosine = np.clip(dot_product / magnitudes, -1.0, 1.0)
	angle_rad = np.arccos(cosine)
	angle_deg = np.degrees(angle_rad)
	
	return float(angle_deg)


def compute_forearm_verticality(
	elbow_3d: np.ndarray,
	wrist_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute angle between forearm and vertical axis.
	
	Based on Cabarkapa et al. (2021):
	- Proficient: 7.9° ± 7.2°
	- Non-proficient: 19.8° ± 17.6°
	- Target range: 0-10°
	
	Args:
		elbow_3d: 3D elbow position [x, y, z]
		wrist_3d: 3D wrist position [x, y, z]
	
	Returns:
		Dict with angle_degrees and confidence (1.0 if valid, 0.0 if invalid)
	"""
	forearm_vector = wrist_3d - elbow_3d
	
	# Vertical unit vector (Y-up coordinate system)
	vertical = np.array([0.0, 1.0, 0.0])
	
	# Compute angle from vertical
	forearm_norm = np.linalg.norm(forearm_vector)
	if forearm_norm == 0:
		return {"angle_degrees": 0.0, "confidence": 0.0}
	
	# Project onto vertical plane (use Y and horizontal components)
	forearm_2d = np.array([forearm_vector[0], forearm_vector[1]])
	vertical_2d = np.array([0.0, 1.0])
	
	dot_product = np.dot(forearm_2d, vertical_2d)
	magnitudes = np.linalg.norm(forearm_2d) * np.linalg.norm(vertical_2d)
	
	if magnitudes == 0:
		return {"angle_degrees": 0.0, "confidence": 0.0}
	
	cosine = np.clip(dot_product / magnitudes, -1.0, 1.0)
	angle_rad = np.arccos(cosine)
	angle_deg = np.degrees(angle_rad)
	
	return {"angle_degrees": float(angle_deg), "confidence": 1.0}


def compute_elbow_flexion(
	shoulder_3d: np.ndarray,
	elbow_3d: np.ndarray,
	wrist_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute elbow flexion/extension angle.
	
	Based on Cabarkapa et al. (2021):
	- Preparatory phase: 70-85° (proficient: 80.5° ± 6.3°)
	- Release phase: 165-180° (extension)
	
	Args:
		shoulder_3d: 3D shoulder position
		elbow_3d: 3D elbow position (joint)
		wrist_3d: 3D wrist position
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle(shoulder_3d, elbow_3d, wrist_3d)
	
	# Confidence based on whether vectors are valid
	ba = shoulder_3d - elbow_3d
	bc = wrist_3d - elbow_3d
	confidence = 1.0 if (np.linalg.norm(ba) > 0 and np.linalg.norm(bc) > 0) else 0.0
	
	return {"angle_degrees": angle, "confidence": confidence}


def compute_knee_flexion(
	hip_3d: np.ndarray,
	knee_3d: np.ndarray,
	ankle_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute knee flexion angle during crouch phase.
	
	Based on Cabarkapa et al. (2021):
	- Target range: 100-120°
	- Proficient: ~108°
	- Non-proficient: typically <100°
	
	Args:
		hip_3d: 3D hip position
		knee_3d: 3D knee position (joint)
		ankle_3d: 3D ankle position
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle(hip_3d, knee_3d, ankle_3d)
	
	# Confidence check
	ba = hip_3d - knee_3d
	bc = ankle_3d - knee_3d
	confidence = 1.0 if (np.linalg.norm(ba) > 0 and np.linalg.norm(bc) > 0) else 0.0
	
	return {"angle_degrees": angle, "confidence": confidence}


def compute_hip_flexion(
	shoulder_3d: np.ndarray,
	hip_3d: np.ndarray,
	knee_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute hip flexion angle for alignment tracking.
	
	Target: 140-160° (maintains proper posture)
	Excessive forward lean reduces balance and power.
	
	Args:
		shoulder_3d: 3D shoulder position
		hip_3d: 3D hip position (joint)
		knee_3d: 3D knee position
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle(shoulder_3d, hip_3d, knee_3d)
	
	ba = shoulder_3d - hip_3d
	bc = knee_3d - hip_3d
	confidence = 1.0 if (np.linalg.norm(ba) > 0 and np.linalg.norm(bc) > 0) else 0.0
	
	return {"angle_degrees": angle, "confidence": confidence}


def compute_shoulder_angle(
	hip_3d: np.ndarray,
	shoulder_3d: np.ndarray,
	elbow_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute shoulder angle (arm elevation).
	
	Target: 120-130° for free-throw (shoulder abduction)
	Measures how elevated the arm is relative to the body.
	
	Args:
		hip_3d: 3D hip position
		shoulder_3d: 3D shoulder position (joint)
		elbow_3d: 3D elbow position
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle(hip_3d, shoulder_3d, elbow_3d)
	
	ba = hip_3d - shoulder_3d
	bc = elbow_3d - shoulder_3d
	confidence = 1.0 if (np.linalg.norm(ba) > 0 and np.linalg.norm(bc) > 0) else 0.0
	
	return {"angle_degrees": angle, "confidence": confidence}


def compute_release_angle(
	ball_trajectory: np.ndarray,
	shot_distance: Optional[float] = None,
) -> Dict[str, float]:
	"""
	Compute ball release angle relative to horizontal.
	
	Based on Okazaki et al. (2012):
	- 2.8m distance: 78.92° ± 5°
	- 4.6m distance: 65.60° ± 5°
	- 6.0m+: 55-65°
	
	Higher arcs needed when shooting closer to basket.
	
	Args:
		ball_trajectory: Array of 3D ball positions [[x, y, z], ...]
			First 2-3 points should be near release
		shot_distance: Optional shot distance in meters for validation
	
	Returns:
		Dict with angle_degrees, confidence, and expected_range
	"""
	if len(ball_trajectory) < 2:
		return {"angle_degrees": 0.0, "confidence": 0.0, "expected_range": None}
	
	# Use first two points to compute release vector
	release_point = ball_trajectory[0]
	next_point = ball_trajectory[1]
	release_vector = next_point - release_point
	
	# Compute horizontal component (X-Z plane)
	horizontal_component = np.sqrt(release_vector[0] ** 2 + release_vector[2] ** 2)
	vertical_component = release_vector[1]
	
	if horizontal_component == 0:
		return {"angle_degrees": 90.0, "confidence": 0.5, "expected_range": None}
	
	# Angle from horizontal (arctan of vertical/horizontal)
	angle_rad = np.arctan2(vertical_component, horizontal_component)
	angle_deg = np.degrees(angle_rad)
	
	# Determine expected range based on shot distance
	expected_range = None
	if shot_distance is not None:
		if shot_distance <= 3.0:
			expected_range = [74.0, 84.0]  # 78.92° ± 5°
		elif shot_distance <= 5.0:
			expected_range = [60.0, 70.0]  # 65.60° ± 5°
		else:
			expected_range = [55.0, 65.0]
	
	confidence = 1.0 if len(ball_trajectory) >= 3 else 0.7
	
	return {
		"angle_degrees": float(angle_deg),
		"confidence": confidence,
		"expected_range": expected_range,
	}


def compute_entry_angle(
	ball_trajectory: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute ball entry angle at rim (relative to horizontal).
	
	Target: 45-55° for optimal entry
	Steeper entry increases chance of scoring.
	
	Args:
		ball_trajectory: Array of 3D ball positions near rim entry
			Last 2-3 points should be near rim
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	if len(ball_trajectory) < 2:
		return {"angle_degrees": 0.0, "confidence": 0.0}
	
	# Use last two points to compute entry vector
	prev_point = ball_trajectory[-2]
	entry_point = ball_trajectory[-1]
	entry_vector = entry_point - prev_point
	
	# Compute horizontal and vertical components
	horizontal_component = np.sqrt(entry_vector[0] ** 2 + entry_vector[2] ** 2)
	vertical_component = -entry_vector[1]  # Negative because ball is descending
	
	if horizontal_component == 0:
		return {"angle_degrees": 90.0, "confidence": 0.5}
	
	angle_rad = np.arctan2(vertical_component, horizontal_component)
	angle_deg = np.degrees(angle_rad)
	
	confidence = 1.0 if len(ball_trajectory) >= 3 else 0.7
	
	return {"angle_degrees": float(angle_deg), "confidence": confidence}


def compute_wrist_angular_velocity(
	wrist_positions: np.ndarray,
	timestamps: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute peak wrist angular velocity post-release.
	
	Target: >2.5 rad/s within 100-150ms after release
	Larger values indicate good wrist flick.
	
	Args:
		wrist_positions: Array of 3D wrist positions [N, 3]
		timestamps: Array of timestamps in seconds [N]
	
	Returns:
		Dict with peak_velocity_rad_per_s, peak_time_ms, and confidence
	"""
	if len(wrist_positions) < 2 or len(timestamps) < 2:
		return {
			"peak_velocity_rad_per_s": 0.0,
			"peak_time_ms": 0.0,
			"confidence": 0.0,
		}
	
	# Compute angular changes
	position_diffs = np.diff(wrist_positions, axis=0)
	time_diffs = np.diff(timestamps)
	
	# Avoid division by zero
	time_diffs = np.where(time_diffs == 0, 1e-6, time_diffs)
	
	# Angular velocity magnitude (rad/s)
	angular_velocities = np.linalg.norm(position_diffs, axis=1) / time_diffs
	
	peak_velocity = float(np.max(angular_velocities))
	peak_idx = int(np.argmax(angular_velocities))
	peak_time_ms = float(timestamps[peak_idx] * 1000.0)
	
	# Confidence based on number of samples and velocity magnitude
	confidence = min(1.0, len(wrist_positions) / 10.0) if peak_velocity > 0 else 0.0
	
	return {
		"peak_velocity_rad_per_s": peak_velocity,
		"peak_time_ms": peak_time_ms,
		"confidence": confidence,
	}


def compute_elbow_height(
	elbow_3d: np.ndarray,
	head_3d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute elbow height relative to head.
	
	Based on Cabarkapa et al. (2021):
	- Proficient: elbow roughly at head height
	- Normative range: 147-153 cm (for adults)
	
	Args:
		elbow_3d: 3D elbow position [x, y, z]
		head_3d: 3D head position [x, y, z]
	
	Returns:
		Dict with height_difference_cm (positive = elbow above head) and confidence
	"""
	height_diff = elbow_3d[1] - head_3d[1]  # Y-axis difference
	
	# Convert to cm (assuming normalized coordinates, may need scale factor)
	# For now, return in normalized units; caller can apply scale
	height_diff_cm = height_diff * 100.0  # Approximate conversion
	
	confidence = 1.0 if np.all(np.isfinite([elbow_3d, head_3d])) else 0.0
	
	return {
		"height_difference_cm": float(height_diff_cm),
		"confidence": confidence,
	}


def smooth_3d_positions(
	positions: np.ndarray,
	window_length: int = 11,
	polyorder: int = 2,
) -> np.ndarray:
	"""
	Apply Savitzky-Golay filter to smooth 3D joint positions.
	
	Used for temporal smoothing of 3D landmarks before computing metrics.
	
	Args:
		positions: Array of 3D positions [N, 3]
		window_length: Window length for filter (must be odd, >= polyorder)
		polyorder: Polynomial order
	
	Returns:
		Smoothed positions [N, 3]
	"""
	if len(positions) < window_length:
		return positions
	
	# Ensure window_length is odd
	if window_length % 2 == 0:
		window_length += 1
	
	# Apply filter to each dimension separately
	smoothed = np.zeros_like(positions)
	for dim in range(positions.shape[1]):
		smoothed[:, dim] = savgol_filter(positions[:, dim], window_length, polyorder)
	
	return smoothed



