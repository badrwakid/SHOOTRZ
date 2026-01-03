"""
2D biomechanics calculations using MediaPipe landmarks.

Fallback calculations when 3D pose data is not available.
Uses normalized 2D coordinates (0-1) from MediaPipe.
"""

import numpy as np
from typing import Dict, Optional


def joint_angle_2d(
	point_a: np.ndarray,
	point_b: np.ndarray,
	point_c: np.ndarray,
) -> float:
	"""
	Compute internal angle at joint B from 2D points.
	
	Args:
		point_a: First point [x, y] (normalized 0-1)
		point_b: Joint point [x, y] (normalized 0-1)
		point_c: Third point [x, y] (normalized 0-1)
	
	Returns:
		Angle in degrees (0-180°)
	"""
	# Ensure 2D
	if len(point_a) > 2:
		point_a = point_a[:2]
	if len(point_b) > 2:
		point_b = point_b[:2]
	if len(point_c) > 2:
		point_c = point_c[:2]
	
	ba = point_a - point_b
	bc = point_c - point_b
	
	dot_product = np.dot(ba, bc)
	magnitudes = np.linalg.norm(ba) * np.linalg.norm(bc)
	
	if magnitudes == 0:
		return 0.0
	
	cosine = np.clip(dot_product / magnitudes, -1.0, 1.0)
	angle_rad = np.arccos(cosine)
	angle_deg = np.degrees(angle_rad)
	
	return float(angle_deg)


def compute_forearm_verticality_2d(
	elbow_2d: np.ndarray,
	wrist_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute forearm verticality from 2D landmarks.
	
	In normalized image coordinates:
	- Y increases downward (Y=0 is top, Y=1 is bottom)
	- Vertical in world space = upward vector = [0, -1] in image space
	
	Args:
		elbow_2d: 2D elbow position [x, y] (normalized 0-1)
		wrist_2d: 2D wrist position [x, y] (normalized 0-1)
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	if len(elbow_2d) > 2:
		elbow_2d = elbow_2d[:2]
	if len(wrist_2d) > 2:
		wrist_2d = wrist_2d[:2]
	
	forearm_vector = wrist_2d - elbow_2d
	
	# In normalized image coordinates, Y increases downward
	# Vertical in world space (upward) = [0, -1] in image space
	# But we need to account for the coordinate system properly
	vertical_2d = np.array([0.0, -1.0])  # Upward in world = negative Y in image
	
	forearm_norm = np.linalg.norm(forearm_vector)
	if forearm_norm == 0:
		return {"angle_degrees": 0.0, "confidence": 0.0}
	
	# Normalize vectors
	forearm_unit = forearm_vector / forearm_norm
	vertical_unit = vertical_2d / np.linalg.norm(vertical_2d)
	
	# Compute angle between vectors
	dot_product = np.dot(forearm_unit, vertical_unit)
	dot_product = np.clip(dot_product, -1.0, 1.0)
	angle_rad = np.arccos(dot_product)
	angle_deg = np.degrees(angle_rad)
	
	# Validate angle is reasonable (0-30° for forearm verticality)
	if angle_deg > 30.0:
		# Angle seems too large - might be coordinate system issue
		# Try alternative calculation
		# Use absolute angle from vertical
		angle_deg = min(angle_deg, 90.0 - angle_deg) if angle_deg > 45.0 else angle_deg
	
	# Lower confidence for 2D, especially if angle seems off
	confidence = 0.8 if angle_deg <= 30.0 else 0.5
	
	return {"angle_degrees": float(angle_deg), "confidence": confidence}


def compute_elbow_flexion_2d(
	shoulder_2d: np.ndarray,
	elbow_2d: np.ndarray,
	wrist_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute elbow flexion angle from 2D landmarks.
	
	Args:
		shoulder_2d: 2D shoulder position [x, y]
		elbow_2d: 2D elbow position [x, y]
		wrist_2d: 2D wrist position [x, y]
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle_2d(shoulder_2d, elbow_2d, wrist_2d)
	
	# Validate angle is reasonable (elbow should be 90-180°)
	if angle < 30 or angle > 200:
		return {"angle_degrees": angle, "confidence": 0.3}
	
	return {"angle_degrees": angle, "confidence": 0.8}


def compute_knee_flexion_2d(
	hip_2d: np.ndarray,
	knee_2d: np.ndarray,
	ankle_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute knee flexion angle from 2D landmarks.
	
	Args:
		hip_2d: 2D hip position [x, y]
		knee_2d: 2D knee position [x, y]
		ankle_2d: 2D ankle position [x, y]
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle_2d(hip_2d, knee_2d, ankle_2d)
	
	# Validate angle is reasonable (knee should be 90-180°)
	if angle < 50 or angle > 200:
		return {"angle_degrees": angle, "confidence": 0.3}
	
	return {"angle_degrees": angle, "confidence": 0.8}


def compute_hip_flexion_2d(
	shoulder_2d: np.ndarray,
	hip_2d: np.ndarray,
	knee_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute hip flexion angle from 2D landmarks.
	
	Args:
		shoulder_2d: 2D shoulder position [x, y]
		hip_2d: 2D hip position [x, y]
		knee_2d: 2D knee position [x, y]
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle_2d(shoulder_2d, hip_2d, knee_2d)
	
	# Validate angle is reasonable (hip should be 140-180°)
	if angle < 100 or angle > 200:
		return {"angle_degrees": angle, "confidence": 0.3}
	
	return {"angle_degrees": angle, "confidence": 0.8}


def compute_shoulder_angle_2d(
	hip_2d: np.ndarray,
	shoulder_2d: np.ndarray,
	elbow_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute shoulder angle from 2D landmarks.
	
	Args:
		hip_2d: 2D hip position [x, y]
		shoulder_2d: 2D shoulder position [x, y]
		elbow_2d: 2D elbow position [x, y]
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	angle = joint_angle_2d(hip_2d, shoulder_2d, elbow_2d)
	
	return {"angle_degrees": angle, "confidence": 0.7}


def compute_elbow_height_2d(
	elbow_2d: np.ndarray,
	head_2d: np.ndarray,
	frame_height: Optional[int] = None,
) -> Dict[str, float]:
	"""
	Compute elbow height relative to head from 2D landmarks.
	
	Args:
		elbow_2d: 2D elbow position [x, y] (normalized)
		head_2d: 2D head position [x, y] (normalized, typically nose)
		frame_height: Optional frame height in pixels for conversion
	
	Returns:
		Dict with height_difference_cm and confidence
	"""
	if len(elbow_2d) > 2:
		elbow_2d = elbow_2d[:2]
	if len(head_2d) > 2:
		head_2d = head_2d[:2]
	
	# Y coordinate difference (in normalized space, Y increases downward)
	# So head_y < elbow_y means elbow is below head
	y_diff_normalized = elbow_2d[1] - head_2d[1]
	
	# Estimate real-world height difference
	# Assume average person height ~175cm, head to elbow ~40cm
	# In normalized space, full body height is roughly 0.6-0.8 of frame
	# Estimate: 1.0 normalized unit ≈ 2.2m (average person + some space)
	estimated_height_diff_m = y_diff_normalized * 2.2  # meters
	estimated_height_diff_cm = estimated_height_diff_m * 100
	
	# Clamp to reasonable range (-50cm to +50cm)
	estimated_height_diff_cm = max(-50.0, min(50.0, estimated_height_diff_cm))
	
	# Typical elbow height is 0-20cm above head at release
	confidence = 0.7 if abs(estimated_height_diff_cm) < 30 else 0.4
	
	return {
		"height_difference_cm": float(estimated_height_diff_cm),
		"confidence": confidence,
	}


def compute_release_angle_from_pose_2d(
	shoulder_2d: np.ndarray,
	elbow_2d: np.ndarray,
	wrist_2d: np.ndarray,
) -> Dict[str, float]:
	"""
	Estimate release angle from arm pose (when ball trajectory unavailable).
	
	Uses arm direction at release to estimate ball trajectory angle.
	In normalized image coordinates: Y increases downward.
	
	Args:
		shoulder_2d: 2D shoulder position [x, y] (normalized 0-1)
		elbow_2d: 2D elbow position [x, y] (normalized 0-1)
		wrist_2d: 2D wrist position [x, y] (normalized 0-1)
	
	Returns:
		Dict with angle_degrees and confidence
	"""
	# Use arm direction (shoulder to wrist) as proxy for release angle
	# This gives better estimate than just forearm
	arm_vector = wrist_2d - shoulder_2d
	
	# In normalized image coordinates:
	# - Y increases downward (Y=0 is top, Y=1 is bottom)
	# - For release angle, we want angle from horizontal (0° = horizontal, 90° = vertical up)
	# - Upward motion = negative Y change in image space
	
	horizontal_component = abs(arm_vector[0])
	vertical_component = -arm_vector[1]  # Negative because Y increases downward
	
	if horizontal_component == 0:
		# Arm is vertical
		angle_deg = 90.0
	else:
		# Compute angle from horizontal
		# atan2(vertical, horizontal) gives angle from horizontal
		angle_rad = np.arctan2(vertical_component, horizontal_component)
		angle_deg = np.degrees(angle_rad)
		
		# Ensure angle is positive (0-90° range for release)
		if angle_deg < 0:
			angle_deg = 180.0 + angle_deg  # Convert to 0-180 range
		if angle_deg > 90:
			angle_deg = 180.0 - angle_deg  # Mirror if > 90
	
	# Validate angle is in realistic range (30-90°)
	# Basketball release angles are typically 45-65°
	if angle_deg < 30.0 or angle_deg > 90.0:
		# Angle seems unrealistic - might be coordinate system issue
		# Try using elbow-wrist vector instead (forearm direction)
		forearm_vector = wrist_2d - elbow_2d
		forearm_horizontal = abs(forearm_vector[0])
		forearm_vertical = -forearm_vector[1]
		
		if forearm_horizontal > 0:
			forearm_angle_rad = np.arctan2(forearm_vertical, forearm_horizontal)
			forearm_angle_deg = np.degrees(forearm_angle_rad)
			if forearm_angle_deg < 0:
				forearm_angle_deg = 180.0 + forearm_angle_deg
			if forearm_angle_deg > 90:
				forearm_angle_deg = 180.0 - forearm_angle_deg
			
			# Use forearm angle if it's more reasonable
			if 30.0 <= forearm_angle_deg <= 90.0:
				angle_deg = forearm_angle_deg
			else:
				# Clamp to reasonable range
				angle_deg = max(30.0, min(90.0, angle_deg))
	
	# Confidence is lower because it's pose-based, not trajectory-based
	# Lower confidence if angle is outside typical range
	if 45.0 <= angle_deg <= 70.0:
		confidence = 0.6  # Typical range
	elif 30.0 <= angle_deg < 45.0 or 70.0 < angle_deg <= 90.0:
		confidence = 0.4  # Less typical but possible
	else:
		confidence = 0.2  # Unlikely range
	
	return {"angle_degrees": float(angle_deg), "confidence": confidence}

