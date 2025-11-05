"""
Grip quality detection based on hand landmarks.

Measures finger spread, palm contact, and ball-hand interaction.
"""

import numpy as np
from typing import Dict, List, Optional


def compute_thumb_index_distance(
	hand_landmarks: np.ndarray,
) -> float:
	"""
	Compute distance between thumb tip and index finger tip.
	
	Target: 2-3cm gap for proper grip
	
	Args:
		hand_landmarks: MediaPipe hand landmarks [21, 3]
			- Index 4: Thumb tip
			- Index 8: Index finger tip
	
	Returns:
		Distance in normalized coordinates (will need scaling factor for real-world)
	"""
	if len(hand_landmarks) < 9:
		return 0.0
	
	thumb_tip = hand_landmarks[4]
	index_tip = hand_landmarks[8]
	
	distance = np.linalg.norm(thumb_tip - index_tip)
	return float(distance)


def detect_palm_contact(
	hand_landmarks: np.ndarray,
	ball_center: Optional[np.ndarray] = None,
	ball_radius: float = 0.12,
) -> Dict[str, float]:
	"""
	Detect if ball is in contact with palm during release.
	
	Minimal palm contact indicates better fingertip control.
	
	Args:
		hand_landmarks: MediaPipe hand landmarks [21, 3]
		ball_center: Optional 3D ball center position
		ball_radius: Ball radius in normalized coordinates (~0.12m = 12cm)
	
	Returns:
		Dict with has_palm_contact (bool as float), contact_time_ratio, and confidence
	"""
	if len(hand_landmarks) < 21:
		return {
			"has_palm_contact": 0.0,
			"contact_time_ratio": 0.0,
			"confidence": 0.0,
		}
	
	# Palm center is landmark 0 (wrist base)
	palm_center = hand_landmarks[0]
	
	# If ball center provided, check distance
	if ball_center is not None:
		distance_to_palm = np.linalg.norm(ball_center - palm_center)
		has_contact = 1.0 if distance_to_palm < ball_radius else 0.0
	else:
		# Fallback: estimate from hand landmarks spread
		# If hand is very open, less likely palm contact
		thumb_index_dist = compute_thumb_index_distance(hand_landmarks)
		has_contact = 1.0 if thumb_index_dist < 0.03 else 0.0
	
	return {
		"has_palm_contact": has_contact,
		"contact_time_ratio": has_contact,  # Simplified for single frame
		"confidence": 1.0 if ball_center is not None else 0.6,
	}


def compute_grip_quality(
	hand_landmarks: np.ndarray,
	ball_center: Optional[np.ndarray] = None,
) -> Dict[str, float]:
	"""
	Compute overall grip quality score (0-1).
	
	Based on:
	- Thumb-index distance (target: 2-3cm)
	- Minimal palm contact
	- Finger spread distribution
	
	Args:
		hand_landmarks: MediaPipe hand landmarks [21, 3]
		ball_center: Optional 3D ball center position
	
	Returns:
		Dict with grip_quality_score, thumb_index_distance, and confidence
	"""
	if len(hand_landmarks) < 21:
		return {
			"grip_quality_score": 0.0,
			"thumb_index_distance": 0.0,
			"confidence": 0.0,
		}
	
	# Compute thumb-index distance
	thumb_index_dist = compute_thumb_index_distance(hand_landmarks)
	
	# Score based on distance (optimal: 0.02-0.04 normalized, ~2-3cm)
	# Convert to real-world: assume hand span ~20cm = 0.2 normalized
	optimal_min = 0.02
	optimal_max = 0.04
	
	if optimal_min <= thumb_index_dist <= optimal_max:
		distance_score = 1.0
	elif thumb_index_dist < optimal_min:
		# Too close - palm contact likely
		distance_score = max(0.0, thumb_index_dist / optimal_min)
	else:
		# Too far - losing grip
		distance_score = max(0.0, 1.0 - (thumb_index_dist - optimal_max) / 0.02)
	
	# Check palm contact
	palm_result = detect_palm_contact(hand_landmarks, ball_center)
	palm_score = 1.0 - palm_result["has_palm_contact"]  # Lower contact = better
	
	# Combine scores (weighted average)
	grip_quality = 0.7 * distance_score + 0.3 * palm_score
	
	confidence = 1.0 if ball_center is not None else 0.7
	
	return {
		"grip_quality_score": float(np.clip(grip_quality, 0.0, 1.0)),
		"thumb_index_distance": thumb_index_dist,
		"confidence": confidence,
	}


def compute_wrist_extension(
	elbow_3d: np.ndarray,
	wrist_3d: np.ndarray,
	middle_finger_mcp: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute wrist extension/flexion angle.
	
	Positive value indicates extension (wrist bent backward).
	Important for follow-through analysis.
	
	Args:
		elbow_3d: 3D elbow position
		wrist_3d: 3D wrist position (joint)
		middle_finger_mcp: 3D middle finger MCP joint position
	
	Returns:
		Dict with extension_angle_degrees and confidence
	"""
	from .biomechanics import joint_angle
	
	angle = joint_angle(elbow_3d, wrist_3d, middle_finger_mcp)
	
	# Wrist extension is typically 60-80° at release
	confidence = 1.0 if np.all(np.isfinite([elbow_3d, wrist_3d, middle_finger_mcp])) else 0.0
	
	return {
		"extension_angle_degrees": angle,
		"confidence": confidence,
	}



