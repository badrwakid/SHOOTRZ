"""
Pose detection validation utilities.

Checks if pose detection is working correctly and all keypoints are detected.
"""

import numpy as np
from typing import Dict, List, Optional


def validate_pose_landmarks(landmarks: np.ndarray) -> Dict[str, any]:
	"""
	Validate that pose landmarks are correctly detected.
	
	Args:
		landmarks: [33, 3] MediaPipe landmarks array
		
	Returns:
		Dict with validation results
	"""
	if landmarks is None or len(landmarks) == 0:
		return {
			"valid": False,
			"error": "No landmarks provided",
			"missing_keypoints": [],
		}
	
	if len(landmarks) < 33:
		return {
			"valid": False,
			"error": f"Expected 33 landmarks, got {len(landmarks)}",
			"missing_keypoints": list(range(len(landmarks), 33)),
		}
	
	# Check for required keypoints for shooting analysis
	required_indices = {
		"nose": 0,
		"right_shoulder": 12,
		"right_elbow": 14,
		"right_wrist": 16,
		"right_hip": 24,
		"right_knee": 26,
		"right_ankle": 28,
	}
	
	missing = []
	low_confidence = []
	
	for name, idx in required_indices.items():
		if idx >= len(landmarks):
			missing.append(name)
			continue
		
		# Check if landmark is at origin (likely not detected)
		landmark = landmarks[idx]
		if np.allclose(landmark[:2], [0, 0], atol=0.01):
			missing.append(name)
		# Check if landmark is out of bounds (normalized should be 0-1)
		elif np.any(landmark[:2] < 0) or np.any(landmark[:2] > 1):
			low_confidence.append(name)
	
	valid = len(missing) == 0
	
	return {
		"valid": valid,
		"missing_keypoints": missing,
		"low_confidence_keypoints": low_confidence,
		"total_landmarks": len(landmarks),
	}


def get_pose_detection_stats(pose_results: List[Dict]) -> Dict[str, any]:
	"""
	Get statistics about pose detection across all frames.
	
	Args:
		pose_results: List of pose detection results
		
	Returns:
		Dict with detection statistics
	"""
	if not pose_results:
		return {
			"total_frames": 0,
			"detected_frames": 0,
			"detection_rate": 0.0,
			"average_confidence": 0.0,
		}
	
	total_frames = len(pose_results)
	detected_frames = 0
	confidences = []
	
	for result in pose_results:
		if result and "landmarks" in result:
			landmarks = result["landmarks"]
			if landmarks is not None and len(landmarks) > 0:
				detected_frames += 1
				if "confidence" in result:
					conf = result["confidence"]
					if conf is not None and len(conf) > 0:
						confidences.append(np.mean(conf))
	
	avg_confidence = np.mean(confidences) if confidences else 0.0
	detection_rate = detected_frames / total_frames if total_frames > 0 else 0.0
	
	return {
		"total_frames": total_frames,
		"detected_frames": detected_frames,
		"detection_rate": detection_rate,
		"average_confidence": float(avg_confidence),
		"frames_with_all_keypoints": detected_frames,  # Simplified
	}

