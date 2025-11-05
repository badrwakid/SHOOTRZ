"""
Ball trajectory analysis for basketball shooting.

Computes arc height, entry angle, release height, and shot distance.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import savgol_filter
from .biomechanics import compute_entry_angle, compute_release_angle


def compute_arc_height(
	ball_trajectory: np.ndarray,
	rim_height: float = 3.05,
) -> Dict[str, float]:
	"""
	Compute maximum height of ball trajectory relative to rim.
	
	Target: 0.5-1.0m above rim (approx 3.6-4.1m total height)
	
	Args:
		ball_trajectory: Array of 3D ball positions [[x, y, z], ...]
		rim_height: Rim height in meters (default: 3.05m)
	
	Returns:
		Dict with arc_height_meters, max_height_meters, and confidence
	"""
	if len(ball_trajectory) == 0:
		return {
			"arc_height_meters": 0.0,
			"max_height_meters": 0.0,
			"confidence": 0.0,
		}
	
	# Extract Y coordinates (height)
	heights = ball_trajectory[:, 1]
	max_height = float(np.max(heights))
	arc_height = max_height - rim_height
	
	confidence = 1.0 if len(ball_trajectory) >= 5 else 0.6
	
	return {
		"arc_height_meters": float(arc_height),
		"max_height_meters": float(max_height),
		"confidence": confidence,
	}


def compute_release_height(
	ball_trajectory: np.ndarray,
	ground_height: float = 0.0,
) -> Dict[str, float]:
	"""
	Compute ball release height relative to ground.
	
	Target: 2.3-2.5m for adult males (at or slightly above head)
	
	Args:
		ball_trajectory: Array of 3D ball positions [[x, y, z], ...]
			First point should be at release
		ground_height: Ground level Y coordinate (default: 0.0)
	
	Returns:
		Dict with release_height_meters and confidence
	"""
	if len(ball_trajectory) == 0:
		return {"release_height_meters": 0.0, "confidence": 0.0}
	
	# First point should be release point
	release_height = ball_trajectory[0, 1] - ground_height
	
	confidence = 1.0 if len(ball_trajectory) >= 2 else 0.5
	
	return {
		"release_height_meters": float(release_height),
		"confidence": confidence,
	}


def smooth_trajectory(
	trajectory: np.ndarray,
	window_length: int = 11,
	polyorder: int = 2,
) -> np.ndarray:
	"""
	Apply Savitzky-Golay filter to smooth ball trajectory.
	
	Reduces jitter for better derivative-based metrics.
	
	Args:
		trajectory: Array of 3D positions [N, 3]
		window_length: Window length for filter (must be odd)
		polyorder: Polynomial order
	
	Returns:
		Smoothed trajectory [N, 3]
	"""
	if len(trajectory) < window_length:
		return trajectory
	
	# Ensure window_length is odd
	if window_length % 2 == 0:
		window_length += 1
	
	smoothed = np.zeros_like(trajectory)
	for dim in range(trajectory.shape[1]):
		smoothed[:, dim] = savgol_filter(trajectory[:, dim], window_length, polyorder)
	
	return smoothed


def compute_shot_distance(
	release_point: np.ndarray,
	rim_position: np.ndarray,
) -> Dict[str, float]:
	"""
	Compute horizontal shot distance from shooter to hoop.
	
	Args:
		release_point: 3D release point [x, y, z]
		rim_position: 3D rim center position [x, y, z]
	
	Returns:
		Dict with distance_meters and confidence
	"""
	# Horizontal distance (X-Z plane only, ignore Y)
	horizontal_diff = release_point[[0, 2]] - rim_position[[0, 2]]
	distance = float(np.linalg.norm(horizontal_diff))
	
	confidence = 1.0 if np.all(np.isfinite([release_point, rim_position])) else 0.0
	
	return {"distance_meters": distance, "confidence": confidence}


def compute_arc_and_entry(
	trajectory: np.ndarray,
	rim_height: float = 3.05,
) -> Dict[str, float]:
	"""
	Compute both arc height and entry angle from trajectory.
	
	Args:
		trajectory: Array of 3D ball positions [[x, y, z], ...]
		rim_height: Rim height in meters
	
	Returns:
		Dict with arc_height, entry_angle, and confidence
	"""
	arc_result = compute_arc_height(trajectory, rim_height)
	entry_result = compute_entry_angle(trajectory)
	
	# Combine confidences
	confidence = min(arc_result["confidence"], entry_result["confidence"])
	
	return {
		"arc_height": arc_result["arc_height_meters"],
		"entry_angle": entry_result["angle_degrees"],
		"confidence": confidence,
	}






