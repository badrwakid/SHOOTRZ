"""
Optimal frame selection for metric computation.

Finds the best frame within each phase for accurate measurements:
- Peak knee flexion for crouch phase
- Maximum arm extension for release phase
- Actual ball release frame when trajectory available
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def find_optimal_crouch_frame(
	pose_results: List[Dict],
	crouch_phase: Dict,
) -> int:
	"""
	Find frame with peak knee flexion (minimum knee angle) in crouch phase.
	
	Args:
		pose_results: List of pose detection results
		crouch_phase: Phase dict with start_frame and end_frame
		
	Returns:
		Frame index with peak knee flexion
	"""
	from ..metrics.biomechanics import joint_angle
	
	start_frame = crouch_phase["start_frame"]
	end_frame = crouch_phase["end_frame"]
	
	knee_angles = []
	
	for frame_idx in range(start_frame, min(end_frame + 1, len(pose_results))):
		pose_lm = pose_results[frame_idx].get("landmarks")
		if pose_lm is None or len(pose_lm) < 29:
			continue
		
		# Get right leg joints (MediaPipe indices: 24=hip, 26=knee, 28=ankle)
		hip = pose_lm[24]
		knee = pose_lm[26]
		ankle = pose_lm[28]
		
		# Compute knee flexion angle
		# Convert to numpy arrays if needed
		if not isinstance(hip, np.ndarray):
			hip = np.array(hip)
		if not isinstance(knee, np.ndarray):
			knee = np.array(knee)
		if not isinstance(ankle, np.ndarray):
			ankle = np.array(ankle)
		
		# Use first 3 elements (x, y, z) if available
		hip_3d = hip[:3] if len(hip) >= 3 else np.append(hip[:2], [0.0])
		knee_3d = knee[:3] if len(knee) >= 3 else np.append(knee[:2], [0.0])
		ankle_3d = ankle[:3] if len(ankle) >= 3 else np.append(ankle[:2], [0.0])
		
		knee_angle = joint_angle(hip_3d, knee_3d, ankle_3d)
		knee_angles.append((frame_idx, knee_angle))
	
	if not knee_angles:
		# Fallback to midpoint
		fallback_frame = start_frame + (end_frame - start_frame) // 2
		log_frame_selection("crouch", fallback_frame, start_frame, end_frame, "midpoint")
		return fallback_frame
	
	# Return frame with minimum knee angle (most flexed)
	optimal_frame = min(knee_angles, key=lambda x: x[1])[0]
	log_frame_selection("crouch", optimal_frame, start_frame, end_frame, "optimal")
	return optimal_frame


def find_optimal_release_frame(
	pose_results: List[Dict],
	release_phase: Dict,
	ball_trajectory: Optional[List[np.ndarray]] = None,
) -> int:
	"""
	Find optimal release frame.
	
	If ball trajectory exists, use actual ball release frame.
	Otherwise, find frame with maximum arm extension (minimum wrist Y).
	
	Args:
		pose_results: List of pose detection results
		release_phase: Phase dict with start_frame and end_frame
		ball_trajectory: Optional ball trajectory positions
		
	Returns:
		Frame index of optimal release frame
	"""
	start_frame = release_phase["start_frame"]
	end_frame = release_phase["end_frame"]
	
	# If ball trajectory exists, find actual release frame
	if ball_trajectory and len(ball_trajectory) > 0:
		# Ball trajectory frame indices should map to pose result frames
		# Find frame where ball starts moving upward (release)
		for i in range(len(ball_trajectory) - 1):
			if i >= len(pose_results):
				break
			
			# Check if ball is moving upward (Y decreasing in normalized coords)
			curr_y = ball_trajectory[i][1] if len(ball_trajectory[i]) > 1 else 0.5
			next_y = ball_trajectory[i + 1][1] if len(ball_trajectory[i + 1]) > 1 else 0.5
			
			# In normalized coords, Y decreases when ball goes up
			if next_y < curr_y:
				# Ball is moving upward - this is likely release
				# Map to pose result frame
				release_frame = min(i, len(pose_results) - 1)
				if start_frame <= release_frame <= end_frame:
					return release_frame
	
	# Fallback: Find frame with maximum arm extension (minimum wrist Y)
	wrist_heights = []
	
	for frame_idx in range(start_frame, min(end_frame + 1, len(pose_results))):
		pose_lm = pose_results[frame_idx].get("landmarks")
		if pose_lm is None or len(pose_lm) < 17:
			continue
		
		# Right wrist Y coordinate (MediaPipe index 16)
		# Lower Y = higher in image (arm more extended)
		wrist = pose_lm[16]
		if len(wrist) >= 2:
			wrist_y = wrist[1]
			wrist_heights.append((frame_idx, wrist_y))
	
	if not wrist_heights:
		# Fallback to midpoint
		fallback_frame = start_frame + (end_frame - start_frame) // 2
		log_frame_selection("release", fallback_frame, start_frame, end_frame, "midpoint")
		return fallback_frame
	
	# Return frame with minimum Y (highest wrist = most extended)
	optimal_frame = min(wrist_heights, key=lambda x: x[1])[0]
	log_frame_selection("release", optimal_frame, start_frame, end_frame, "optimal")
	return optimal_frame


def find_optimal_stance_frame(
	pose_results: List[Dict],
	stance_phase: Dict,
) -> int:
	"""
	Find optimal frame for stance phase.
	
	Uses frame with maximum knee extension (least flexed).
	
	Args:
		pose_results: List of pose detection results
		stance_phase: Phase dict with start_frame and end_frame
		
	Returns:
		Frame index with maximum knee extension
	"""
	from ..metrics.biomechanics import joint_angle
	
	start_frame = stance_phase["start_frame"]
	end_frame = stance_phase["end_frame"]
	
	knee_angles = []
	
	for frame_idx in range(start_frame, min(end_frame + 1, len(pose_results))):
		pose_lm = pose_results[frame_idx].get("landmarks")
		if pose_lm is None or len(pose_lm) < 29:
			continue
		
		# Get right leg joints
		hip = pose_lm[24]
		knee = pose_lm[26]
		ankle = pose_lm[28]
		
		if not isinstance(hip, np.ndarray):
			hip = np.array(hip)
		if not isinstance(knee, np.ndarray):
			knee = np.array(knee)
		if not isinstance(ankle, np.ndarray):
			ankle = np.array(ankle)
		
		hip_3d = hip[:3] if len(hip) >= 3 else np.append(hip[:2], [0.0])
		knee_3d = knee[:3] if len(knee) >= 3 else np.append(knee[:2], [0.0])
		ankle_3d = ankle[:3] if len(ankle) >= 3 else np.append(ankle[:2], [0.0])
		
		knee_angle = joint_angle(hip_3d, knee_3d, ankle_3d)
		knee_angles.append((frame_idx, knee_angle))
	
	if not knee_angles:
		# Fallback to first frame
		return start_frame
	
	# Return frame with maximum angle (least flexed = most extended)
	optimal_frame = max(knee_angles, key=lambda x: x[1])[0]
	return optimal_frame


def validate_frame_index(frame_idx: int, total_frames: int) -> bool:
	"""
	Validate that frame index is within bounds.
	
	Args:
		frame_idx: Frame index to validate
		total_frames: Total number of frames
		
	Returns:
		True if valid, False otherwise
	"""
	return 0 <= frame_idx < total_frames

