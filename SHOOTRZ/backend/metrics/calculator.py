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

		# 1. Forearm Verticality (preparatory phase)
		crouch_phase = phase_map.get("crouch")
		if crouch_phase and use_3d_data:
			prep_frame = crouch_phase["start_frame"] + (crouch_phase["end_frame"] - crouch_phase["start_frame"]) // 2
			if prep_frame < len(landmarks_3d):
				lm = landmarks_3d[prep_frame]
				# Right arm (assuming right-handed shot)
				if len(lm) > 16:
					elbow = lm[14]  # Right elbow
					wrist = lm[16]  # Right wrist
					result = compute_forearm_verticality(elbow, wrist)
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
		for phase_name in ["crouch", "release"]:
			phase_info = phase_map.get(phase_name)
			if phase_info and use_3d_data:
				phase_frame = phase_info["start_frame"] + (phase_info["end_frame"] - phase_info["start_frame"]) // 2
				if phase_frame < len(landmarks_3d):
					lm = landmarks_3d[phase_frame]
					if len(lm) > 16:
						shoulder = lm[12]  # Right shoulder
						elbow = lm[14]  # Right elbow
						wrist = lm[16]  # Right wrist
						result = compute_elbow_flexion(shoulder, elbow, wrist)
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
		if crouch_phase and use_3d_data:
			crouch_frame = crouch_phase["start_frame"] + (crouch_phase["end_frame"] - crouch_phase["start_frame"]) // 2
			if crouch_frame < len(landmarks_3d):
				lm = landmarks_3d[crouch_frame]
				if len(lm) > 28:
					hip = lm[24]  # Right hip
					knee = lm[26]  # Right knee
					ankle = lm[28]  # Right ankle
					result = compute_knee_flexion(hip, knee, ankle)
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
		if crouch_phase and use_3d_data:
			crouch_frame = crouch_phase["start_frame"] + (crouch_phase["end_frame"] - crouch_phase["start_frame"]) // 2
			if crouch_frame < len(landmarks_3d):
				lm = landmarks_3d[crouch_frame]
				if len(lm) > 26:
					shoulder = lm[12]  # Right shoulder
					hip = lm[24]  # Right hip
					knee = lm[26]  # Right knee
					result = compute_hip_flexion(shoulder, hip, knee)
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
		if crouch_phase and use_3d_data:
			crouch_frame = crouch_phase["start_frame"] + (crouch_phase["end_frame"] - crouch_phase["start_frame"]) // 2
			if crouch_frame < len(landmarks_3d):
				lm = landmarks_3d[crouch_frame]
				if len(lm) > 16:
					hip = lm[24]  # Right hip
					shoulder = lm[12]  # Right shoulder
					elbow = lm[14]  # Right elbow
					result = compute_shoulder_angle(hip, shoulder, elbow)
					metrics.append({
						"metric_name": "shoulder_angle",
						"value": result["angle_degrees"],
						"unit": "degrees",
						"confidence": result["confidence"],
						"phase": "crouch",
						"timestamp_ms": pose_results[crouch_frame].get("timestamp_ms", 0),
						"frame_idx": crouch_frame,
					})

		# 6. Elbow Height
		if crouch_phase and use_3d_data:
			crouch_frame = crouch_phase["start_frame"] + (crouch_phase["end_frame"] - crouch_phase["start_frame"]) // 2
			if crouch_frame < len(landmarks_3d):
				lm = landmarks_3d[crouch_frame]
				if len(lm) > 14:
					head = lm[0]  # Nose (approximation for head)
					elbow = lm[14]  # Right elbow
					result = compute_elbow_height(elbow, head)
					metrics.append({
						"metric_name": "elbow_height",
						"value": result["height_difference_cm"],
						"unit": "cm",
						"confidence": result["confidence"],
						"phase": "crouch",
						"timestamp_ms": pose_results[crouch_frame].get("timestamp_ms", 0),
						"frame_idx": crouch_frame,
					})

		# 7. Release Angle (from ball trajectory)
		if ball_trajectory and len(ball_trajectory) >= 2:
			# Smooth trajectory
			ball_array = np.array(ball_trajectory)
			if len(ball_array) >= 5:
				ball_array = smooth_trajectory(ball_array)

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
					"timestamp_ms": pose_results[0].get("timestamp_ms", 0) if pose_results else 0,
					"frame_idx": 0,
					"shot_distance": shot_distance,
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
			result = compute_arc_height(ball_array)
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
				metrics.append({
					"metric_name": "release_height",
					"value": result["release_height_meters"],
					"unit": "meters",
					"confidence": result["confidence"],
					"phase": "release",
					"timestamp_ms": pose_results[0].get("timestamp_ms", 0) if pose_results else 0,
					"frame_idx": 0,
				})

		# 11. Wrist Angular Velocity (post-release)
		release_phase = phase_map.get("release")
		if release_phase and use_3d_data:
			# Get wrist positions for ~10 frames after release
			release_frame = release_phase["end_frame"]
			wrist_positions = []
			timestamps = []
			for i in range(release_frame, min(release_frame + 10, len(landmarks_3d))):
				lm = landmarks_3d[i]
				if len(lm) > 16:
					wrist_positions.append(lm[16])  # Right wrist
					timestamps.append(pose_results[i].get("timestamp_ms", i * 33.33) / 1000.0)

			if len(wrist_positions) >= 2:
				result = compute_wrist_angular_velocity(
					np.array(wrist_positions),
					np.array(timestamps),
				)
				if result["confidence"] > 0:
					metrics.append({
						"metric_name": "wrist_angular_velocity",
						"value": result["peak_velocity_rad_per_s"],
						"unit": "rad/s",
						"confidence": result["confidence"],
						"phase": "release",
						"timestamp_ms": result["peak_time_ms"],
						"frame_idx": release_frame,
					})

		# 12. Grip Quality (from hand landmarks)
		if hand_results and release_phase:
			release_frame = release_phase["start_frame"]
			for hand_result in hand_results:
				if hand_result.get("frame_idx") == release_frame:
					hands = hand_result.get("hands", [])
					for hand in hands:
						if hand.get("handedness") == "Right":  # Shooting hand
							landmarks = hand.get("landmarks")
							if landmarks is not None:
								# Get ball center if available
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
										"timestamp_ms": pose_results[release_frame].get("timestamp_ms", 0),
										"frame_idx": release_frame,
									})
					break

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



