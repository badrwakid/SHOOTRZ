"""
Input validation utilities for API endpoints and processing functions.
"""

import numpy as np
from typing import Optional, Tuple
from pathlib import Path


def validate_metric_value(value: float, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
	"""Validate metric value is within expected range."""
	if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
		return False
	
	if min_val is not None and value < min_val:
		return False
	
	if max_val is not None and value > max_val:
		return False
	
	return True


def validate_landmarks(landmarks: np.ndarray, expected_count: int = 33) -> Tuple[bool, Optional[str]]:
	"""Validate pose landmarks array."""
	if landmarks is None:
		return False, "Landmarks cannot be None"
	
	if not isinstance(landmarks, np.ndarray):
		return False, "Landmarks must be numpy array"
	
	if len(landmarks.shape) != 2:
		return False, "Landmarks must be 2D array"
	
	if landmarks.shape[0] != expected_count:
		return False, f"Expected {expected_count} landmarks, got {landmarks.shape[0]}"
	
	if landmarks.shape[1] < 2:
		return False, "Landmarks must have at least 2 dimensions (x, y)"
	
	# Check for NaN or infinite values
	if np.any(np.isnan(landmarks)) or np.any(np.isinf(landmarks)):
		return False, "Landmarks contain NaN or infinite values"
	
	return True, None


def validate_trajectory(trajectory: list, min_points: int = 2) -> Tuple[bool, Optional[str]]:
	"""Validate ball trajectory."""
	if not trajectory:
		return False, "Trajectory is empty"
	
	if len(trajectory) < min_points:
		return False, f"Trajectory must have at least {min_points} points"
	
	for point in trajectory:
		if not isinstance(point, (list, np.ndarray)):
			return False, "Trajectory points must be arrays"
		if len(point) < 2:
			return False, "Trajectory points must have at least 2 coordinates"
	
	return True, None


def validate_video_path(video_path: str) -> Tuple[bool, Optional[str]]:
	"""Validate video file path."""
	path = Path(video_path)
	
	if not path.exists():
		return False, f"Video file does not exist: {video_path}"
	
	if not path.is_file():
		return False, f"Path is not a file: {video_path}"
	
	# Check file extension
	valid_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
	if path.suffix.lower() not in valid_extensions:
		return False, f"Unsupported video format: {path.suffix}"
	
	return True, None


def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
	"""Validate user ID format."""
	if not user_id:
		return False, "User ID cannot be empty"
	
	if not isinstance(user_id, str):
		return False, "User ID must be a string"
	
	# UUIDs are 36 characters with hyphens
	if len(user_id) < 10:
		return False, "User ID too short"
	
	return True, None



