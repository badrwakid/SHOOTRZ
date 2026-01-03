"""
Comprehensive metrics calculator for basketball shooting analysis.

Orchestrates all metric computations using biomechanics module.
Computes 16+ metrics with phase labels and confidence scores.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .biomechanics import (
	compute_forearm_verticality,
	compute_elbow_flexion,
	compute_knee_flexion,
	compute_hip_flexion,
	compute_shoulder_angle,
	compute_release_angle,
	compute_entry_angle,
	compute_wrist_angular_velocity,
	compute_elbow_height,
	smooth_3d_positions,
)

from .trajectory import (
	compute_arc_height,
	compute_release_height,
	compute_shot_distance,
	smooth_trajectory,
)

from .grip import (
	compute_grip_quality,
	compute_wrist_extension,
)

from ..inference.phase_detector import PhaseDetector, ShootingPhase


class MetricsCalculator:
	"""
	Orchestrates computation of all shooting metrics.
	"""

	def __init__(self, use_3d: bool = True):
		"""
		Initialize metrics calculator.
		
		Args:
			use_3d: If True, use 3D landmarks; otherwise use 2D projections
		"""
		self.use_3d = use_3d
		self.phase_detector = PhaseDetector()

	def compute_all_metrics(
		self,
		pose_results: List[Dict[str, any]],
		hand_results: Optional[List[Dict[str, any]]] = None,
		ball_trajectory: Optional[List[np.ndarray]] = None,
		pose_3d: Optional[List[np.ndarray]] = None,
		shot_distance: Optional[float] = None,
		rim_position: Optional[np.ndarray] = None,
	) -> List[Dict[str, any]]:
		"""
		Compute all metrics from pose, hand, and ball data.
		
		Args:
			pose_results: List of 2D pose detection results
			hand_results: Optional list of hand detection results
			ball_trajectory: Optional list of 3D ball positions
			pose_3d: Optional list of 3D pose landmarks [N, 33, 3]
			shot_distance: Optional shot distance in meters
			rim_position: Optional 3D rim position for distance calculation
		
		Returns:
			List of metric dictionaries: [{
				'metric_name': str,
				'value': float,
				'unit': str,
				'confidence': float,
				'phase': str,
				'timestamp_ms': float,
				'frame_idx': int
			}]
		"""
		metrics = []

		if not pose_results:
			return metrics

		# Determine which landmarks to use (3D if available, else 2D)
		if pose_3d and len(pose_3d) == len(pose_results):
			landmarks_3d = pose_3d
			use_3d_data = True
		else:
			# Use 2D landmarks (will need projection for 3D calculations)
			landmarks_3d = None
			use_3d_data = False
		
		# Import 2D fallback functions
		from .biomechanics_2d import (
			compute_forearm_verticality_2d,
			compute_elbow_flexion_2d,
			compute_knee_flexion_2d,
			compute_hip_flexion_2d,
			compute_shoulder_angle_2d,
			compute_elbow_height_2d,
			compute_release_angle_from_pose_2d,
		)

		# Detect phases
		phases = self.phase_detector.detect_phases(pose_results, ball_trajectory)
		phase_map = {p["phase"].value: p for p in phases}

		# Get phase at specific frame
		def get_phase_at_frame(frame_idx: int) -> str:
			for phase_info in phases:
				if phase_info["start_frame"] <= frame_idx <= phase_info["end_frame"]:
					return phase_info["phase"].value
			return "unknown"

		# Prepare 3D landmark arrays if available
		if use_3d_data and landmarks_3d is not None:
			# Smooth 3D landmarks
			landmarks_3d_smoothed = []
			for frame_landmarks in landmarks_3d:
				smoothed = smooth_3d_positions(frame_landmarks)
				landmarks_3d_smoothed.append(smoothed)
			landmarks_3d = landmarks_3d_smoothed

		# Import optimal frame selector
		from ..utils.frame_selector import find_optimal_crouch_frame, validate_frame_index
		
		# 1. Forearm Verticality (preparatory phase)
		crouch_phase = phase_map.get("crouch")
		if crouch_phase:
			# Find optimal frame with peak knee flexion
			prep_frame = find_optimal_crouch_frame(pose_results, crouch_phase)
			if validate_frame_index(prep_frame, len(pose_results)):
				pose_lm = pose_results[prep_frame]["landmarks"]
				# Right arm (assuming right-handed shot)
				# MediaPipe indices: 14=right elbow, 16=right wrist
				if len(pose_lm) > 16:
					if use_3d_data and landmarks_3d and prep_frame < len(landmarks_3d):
						lm = landmarks_3d[prep_frame]
						elbow = lm[14]  # Right elbow
						wrist = lm[16]  # Right wrist
						result = compute_forearm_verticality(elbow, wrist)
					else:
						# 2D fallback
						elbow = pose_lm[14][:2]  # Right elbow [x, y]
						wrist = pose_lm[16][:2]  # Right wrist [x, y]
						result = compute_forearm_verticality_2d(elbow, wrist)
					
					if result["confidence"] > 0:
						metrics.append({
							"metric_name": "forearm_verticality",
							"value": result["angle_degrees"],
							"unit": "degrees",
							"confidence": result["confidence"],
							"phase": "crouch",
							"timestamp_ms": pose_results[prep_frame].get("timestamp_ms", 0),
							"frame_idx": prep_frame,
						})

		# 2. Elbow Flexion (preparatory and release)
		from ..utils.frame_selector import find_optimal_release_frame
		
		for phase_name in ["crouch", "release"]:
			phase_info = phase_map.get(phase_name)
			if phase_info:
				# Find optimal frame for each phase
				if phase_name == "crouch":
					phase_frame = find_optimal_crouch_frame(pose_results, phase_info)
				elif phase_name == "release":
					phase_frame = find_optimal_release_frame(pose_results, phase_info, ball_trajectory)
				else:
					# Fallback to midpoint
					phase_frame = phase_info["start_frame"] + (phase_info["end_frame"] - phase_info["start_frame"]) // 2
				
				if validate_frame_index(phase_frame, len(pose_results)):
					pose_lm = pose_results[phase_frame]["landmarks"]
					if len(pose_lm) > 16:
						if use_3d_data and landmarks_3d and phase_frame < len(landmarks_3d):
							lm = landmarks_3d[phase_frame]
							shoulder = lm[12]  # Right shoulder
							elbow = lm[14]  # Right elbow
							wrist = lm[16]  # Right wrist
							result = compute_elbow_flexion(shoulder, elbow, wrist)
						else:
							# 2D fallback
							shoulder = pose_lm[12][:2]  # Right shoulder
							elbow = pose_lm[14][:2]  # Right elbow
							wrist = pose_lm[16][:2]  # Right wrist
							result = compute_elbow_flexion_2d(shoulder, elbow, wrist)
						
						if result["confidence"] > 0:
							metric_name = f"elbow_flexion_{phase_name}"
							metrics.append({
								"metric_name": metric_name,
								"value": result["angle_degrees"],
								"unit": "degrees",
								"confidence": result["confidence"],
								"phase": phase_name,
								"timestamp_ms": pose_results[phase_frame].get("timestamp_ms", 0),
								"frame_idx": phase_frame,
							})

		# 3. Knee Flexion (crouch phase)
		if crouch_phase:
			# Find optimal frame with peak knee flexion
			crouch_frame = find_optimal_crouch_frame(pose_results, crouch_phase)
			if validate_frame_index(crouch_frame, len(pose_results)):
				pose_lm = pose_results[crouch_frame]["landmarks"]
				if len(pose_lm) > 27:
					if use_3d_data and landmarks_3d and crouch_frame < len(landmarks_3d):
						lm = landmarks_3d[crouch_frame]
						hip = lm[24]  # Right hip
						knee = lm[26]  # Right knee
						ankle = lm[28]  # Right ankle
						result = compute_knee_flexion(hip, knee, ankle)
					else:
						# 2D fallback
						hip = pose_lm[24][:2]  # Right hip
						knee = pose_lm[26][:2]  # Right knee
						ankle = pose_lm[28][:2]  # Right ankle
						result = compute_knee_flexion_2d(hip, knee, ankle)
					
					if result["confidence"] > 0:
						metrics.append({
							"metric_name": "knee_flexion",
							"value": result["angle_degrees"],
							"unit": "degrees",
							"confidence": result["confidence"],
							"phase": "crouch",
							"timestamp_ms": pose_results[crouch_frame].get("timestamp_ms", 0),
							"frame_idx": crouch_frame,
						})

		# 4. Hip Flexion
		if crouch_phase:
			# Use same optimal crouch frame
			crouch_frame = find_optimal_crouch_frame(pose_results, crouch_phase)
			if validate_frame_index(crouch_frame, len(pose_results)):
				pose_lm = pose_results[crouch_frame]["landmarks"]
				if len(pose_lm) > 26:
					if use_3d_data and landmarks_3d and crouch_frame < len(landmarks_3d):
						lm = landmarks_3d[crouch_frame]
						shoulder = lm[12]  # Right shoulder
						hip = lm[24]  # Right hip
						knee = lm[26]  # Right knee
						result = compute_hip_flexion(shoulder, hip, knee)
					else:
						# 2D fallback
						shoulder = pose_lm[12][:2]  # Right shoulder
						hip = pose_lm[24][:2]  # Right hip
						knee = pose_lm[26][:2]  # Right knee
						result = compute_hip_flexion_2d(shoulder, hip, knee)
					
					if result["confidence"] > 0:
						metrics.append({
							"metric_name": "hip_flexion",
							"value": result["angle_degrees"],
							"unit": "degrees",
							"confidence": result["confidence"],
							"phase": "crouch",
							"timestamp_ms": pose_results[crouch_frame].get("timestamp_ms", 0),
							"frame_idx": crouch_frame,
						})

		# 5. Shoulder Angle
		if crouch_phase:
			# Use same optimal crouch frame
			crouch_frame = find_optimal_crouch_frame(pose_results, crouch_phase)
			if validate_frame_index(crouch_frame, len(pose_results)):
				pose_lm = pose_results[crouch_frame]["landmarks"]
				if len(pose_lm) > 24:
					if use_3d_data and landmarks_3d and crouch_frame < len(landmarks_3d):
						lm = landmarks_3d[crouch_frame]
						hip = lm[24]  # Right hip
						shoulder = lm[12]  # Right shoulder
						elbow = lm[14]  # Right elbow
						result = compute_shoulder_angle(hip, shoulder, elbow)
					else:
						# 2D fallback
						hip = pose_lm[24][:2]  # Right hip
						shoulder = pose_lm[12][:2]  # Right shoulder
						elbow = pose_lm[14][:2]  # Right elbow
						result = compute_shoulder_angle_2d(hip, shoulder, elbow)
					
					if result["confidence"] > 0:
						metrics.append({
							"metric_name": "shoulder_angle",
							"value": result["angle_degrees"],
							"unit": "degrees",
							"confidence": result["confidence"],
							"phase": "crouch",
							"timestamp_ms": pose_results[crouch_frame].get("timestamp_ms", 0),
							"frame_idx": crouch_frame,
						})

		# 6. Elbow Height (at release phase, not crouch)
		release_phase = phase_map.get("release")
		if release_phase:
			# Find optimal release frame (max arm extension or actual ball release)
			release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
			if validate_frame_index(release_frame, len(pose_results)):
				pose_lm = pose_results[release_frame]["landmarks"]
				if len(pose_lm) > 13:
					if use_3d_data and landmarks_3d and release_frame < len(landmarks_3d):
						lm = landmarks_3d[release_frame]
						head = lm[0]  # Nose (approximation for head)
						elbow = lm[14]  # Right elbow
						result = compute_elbow_height(elbow, head)
					else:
						# 2D fallback
						head = pose_lm[0][:2]  # Nose
						elbow = pose_lm[14][:2]  # Right elbow
						result = compute_elbow_height_2d(elbow, head)
					
					if result["confidence"] > 0:
						metrics.append({
							"metric_name": "elbow_height",
							"value": result["height_difference_cm"],
							"unit": "cm",
							"confidence": result["confidence"],
							"phase": "release",
							"timestamp_ms": pose_results[release_frame].get("timestamp_ms", 0),
							"frame_idx": release_frame,
						})

		# 7. Release Angle (from ball trajectory or pose fallback)
		release_angle_computed = False
		if ball_trajectory and len(ball_trajectory) >= 2:
			# Smooth trajectory
			ball_array = np.array(ball_trajectory)
			if len(ball_array) >= 5:
				ball_array = smooth_trajectory(ball_array)

			# Find actual release frame from ball trajectory
			release_phase = phase_map.get("release")
			actual_release_frame = 0
			if release_phase:
				actual_release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
			else:
				# Find first frame where ball moves upward
				for i in range(len(ball_trajectory) - 1):
					if i >= len(pose_results):
						break
					curr_y = ball_trajectory[i][1] if len(ball_trajectory[i]) > 1 else 0.5
					next_y = ball_trajectory[i + 1][1] if len(ball_trajectory[i + 1]) > 1 else 0.5
					if next_y < curr_y:  # Ball moving up
						actual_release_frame = min(i, len(pose_results) - 1)
						break

			# Compute shot distance if not provided
			if shot_distance is None and rim_position is not None and len(ball_array) > 0:
				release_point = ball_array[0]
				dist_result = compute_shot_distance(release_point, rim_position)
				shot_distance = dist_result.get("distance_meters")

			result = compute_release_angle(ball_array, shot_distance)
			if result["confidence"] > 0:
				metrics.append({
					"metric_name": "release_angle",
					"value": result["angle_degrees"],
					"unit": "degrees",
					"confidence": result["confidence"],
					"phase": "release",
					"timestamp_ms": pose_results[actual_release_frame].get("timestamp_ms", 0) if actual_release_frame < len(pose_results) else 0,
					"frame_idx": actual_release_frame,
					"shot_distance": shot_distance,
				})
				release_angle_computed = True
		
		# Fallback: Estimate release angle from pose if no ball trajectory
		if not release_angle_computed:
			release_phase = phase_map.get("release")
			if release_phase:
				# Find optimal release frame (max arm extension)
				release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
				if validate_frame_index(release_frame, len(pose_results)):
					pose_lm = pose_results[release_frame]["landmarks"]
					if len(pose_lm) > 16:
						shoulder = pose_lm[12][:2]  # Right shoulder
						elbow = pose_lm[14][:2]  # Right elbow
						wrist = pose_lm[16][:2]  # Right wrist
						result = compute_release_angle_from_pose_2d(shoulder, elbow, wrist)
						if result["confidence"] > 0:
							metrics.append({
								"metric_name": "release_angle",
								"value": result["angle_degrees"],
								"unit": "degrees",
								"confidence": result["confidence"],
								"phase": "release",
								"timestamp_ms": pose_results[release_frame].get("timestamp_ms", 0),
								"frame_idx": release_frame,
								"note": "estimated_from_pose",
							})

		# 8. Entry Angle (from ball trajectory)
		if ball_trajectory and len(ball_trajectory) >= 3:
			ball_array = np.array(ball_trajectory)
			if len(ball_array) >= 5:
				ball_array = smooth_trajectory(ball_array)
			result = compute_entry_angle(ball_array)
			if result["confidence"] > 0:
				metrics.append({
					"metric_name": "entry_angle",
					"value": result["angle_degrees"],
					"unit": "degrees",
					"confidence": result["confidence"],
					"phase": "landing",
					"timestamp_ms": pose_results[-1].get("timestamp_ms", 0) if pose_results else 0,
					"frame_idx": len(pose_results) - 1 if pose_results else 0,
				})

		# 9. Arc Height
		if ball_trajectory and len(ball_trajectory) >= 3:
			ball_array = np.array(ball_trajectory)
			# Try to get frame dimensions from pose results if available
			# For now, assume normalized coordinates and estimate
			result = compute_arc_height(ball_array, frame_height=None)
			if result["confidence"] > 0:
				metrics.append({
					"metric_name": "arc_height",
					"value": result["arc_height_meters"],
					"unit": "meters",
					"confidence": result["confidence"],
					"phase": "release",
					"timestamp_ms": pose_results[len(pose_results) // 2].get("timestamp_ms", 0) if pose_results else 0,
					"frame_idx": len(pose_results) // 2 if pose_results else 0,
				})

		# 10. Release Height
		if ball_trajectory and len(ball_trajectory) >= 1:
			ball_array = np.array(ball_trajectory)
			result = compute_release_height(ball_array)
			if result["confidence"] > 0:
				# Use actual release frame if available
				release_phase = phase_map.get("release")
				release_frame = 0
				if release_phase:
					release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
				
				metrics.append({
					"metric_name": "release_height",
					"value": result["release_height_meters"],
					"unit": "meters",
					"confidence": result["confidence"],
					"phase": "release",
					"timestamp_ms": pose_results[release_frame].get("timestamp_ms", 0) if release_frame < len(pose_results) else 0,
					"frame_idx": release_frame,
				})

		# 11. Wrist Angular Velocity (post-release)
		release_phase = phase_map.get("release")
		if release_phase:
			# Get optimal release frame
			release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
			# Get wrist positions for ~10 frames after release
			wrist_positions = []
			timestamps = []
			
			for i in range(release_frame, min(release_frame + 10, len(pose_results))):
				if use_3d_data and landmarks_3d and i < len(landmarks_3d):
					lm = landmarks_3d[i]
					if len(lm) > 16:
						wrist_positions.append(lm[16])  # Right wrist 3D
						timestamps.append(pose_results[i].get("timestamp_ms", i * 33.33) / 1000.0)
				else:
					# 2D fallback - use 2D wrist position with estimated Z=0
					pose_lm = pose_results[i]["landmarks"]
					if len(pose_lm) > 16:
						wrist_2d = pose_lm[16][:2]  # [x, y]
						wrist_3d_est = np.array([wrist_2d[0], wrist_2d[1], 0.0])  # Estimate Z=0
						wrist_positions.append(wrist_3d_est)
						timestamps.append(pose_results[i].get("timestamp_ms", i * 33.33) / 1000.0)

			if len(wrist_positions) >= 2:
				result = compute_wrist_angular_velocity(
					np.array(wrist_positions),
					np.array(timestamps),
				)
				if result["confidence"] > 0:
					# Lower confidence for 2D estimates
					confidence = result["confidence"] * (0.7 if not use_3d_data else 1.0)
					metrics.append({
						"metric_name": "wrist_angular_velocity",
						"value": result["peak_velocity_rad_per_s"],
						"unit": "rad/s",
						"confidence": confidence,
						"phase": "release",
						"timestamp_ms": result["peak_time_ms"],
						"frame_idx": release_frame,
					})

		# 12. Grip Quality (from hand landmarks)
		if hand_results and release_phase:
			# Get optimal release frame
			release_frame = find_optimal_release_frame(pose_results, release_phase, ball_trajectory)
			# Try to find hand data near release frame (within 5 frames)
			for hand_result in hand_results:
				frame_idx = hand_result.get("frame_idx", -1)
				if abs(frame_idx - release_frame) <= 5:
					hands = hand_result.get("hands", [])
					for hand in hands:
						# Try right hand first, then any hand if right not available
						if hand.get("handedness") in ["Right", "right", "R"] or len(hands) == 1:
							landmarks = hand.get("landmarks")
							if landmarks is not None and len(landmarks) > 0:
								# Get ball center if available (optional)
								ball_center = None
								if ball_trajectory and len(ball_trajectory) > release_frame:
									ball_center = np.array(ball_trajectory[release_frame])

								result = compute_grip_quality(
									np.array(landmarks),
									ball_center,
								)
								if result["confidence"] > 0:
									metrics.append({
										"metric_name": "grip_quality",
										"value": result["grip_quality_score"],
										"unit": "score",
										"confidence": result["confidence"],
										"phase": "release",
										"timestamp_ms": pose_results[release_frame].get("timestamp_ms", 0) if release_frame < len(pose_results) else 0,
										"frame_idx": release_frame,
									})
									break  # Found hand, stop searching
							break
					if any(m.get("metric_name") == "grip_quality" for m in metrics):
						break

		# Debug logging (only in development)
		import os
		if os.getenv("DEBUG_METRICS", "false").lower() == "true":
			from ..utils.metric_debug import log_metric_computation
			log_metric_computation(metrics, "computation")
		
		return metrics

	def compute_shot_distance_estimate(
		self,
		release_point: np.ndarray,
		rim_position: Optional[np.ndarray] = None,
	) -> Optional[float]:
		"""
		Estimate shot distance if rim position is available.
		
		Args:
			release_point: 3D release point
			rim_position: Optional 3D rim position
		
		Returns:
			Distance in meters or None
		"""
		if rim_position is None:
			return None

		result = compute_shot_distance(release_point, rim_position)
		return result.get("distance_meters") if result["confidence"] > 0 else None



