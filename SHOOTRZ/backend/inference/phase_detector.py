"""
Phase detection state machine for basketball shooting motion.

Detects: stance → crouch → release → landing phases using ball velocity and limb motion.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ShootingPhase(Enum):
	"""Shooting motion phases."""
	STANCE = "stance"
	CROUCH = "crouch"
	RELEASE = "release"
	LANDING = "landing"
	UNKNOWN = "unknown"


class PhaseDetector:
	"""
	Rule-based state machine to detect shooting phases.
	
	Uses:
	- Ball vertical velocity (release detection)
	- Knee flexion (crouch detection)
	- Wrist position (release detection)
	- Ball position (trajectory start)
	"""

	def __init__(
		self,
		ball_velocity_threshold: float = 2.0,
		knee_flexion_threshold: float = 100.0,
		min_phase_frames: int = 5,
	):
		"""
		Initialize phase detector.
		
		Args:
			ball_velocity_threshold: Minimum ball vertical velocity for release (m/s or normalized)
			knee_flexion_threshold: Minimum knee flexion angle for crouch (degrees)
			min_phase_frames: Minimum frames required for a phase
		"""
		self.ball_velocity_threshold = ball_velocity_threshold
		self.knee_flexion_threshold = knee_flexion_threshold
		self.min_phase_frames = min_phase_frames

	def compute_ball_velocity(
		self,
		ball_positions: List[np.ndarray],
		timestamps: Optional[List[float]] = None,
	) -> np.ndarray:
		"""
		Compute ball vertical velocity at each frame.
		
		Args:
			ball_positions: List of 3D ball positions
			timestamps: Optional timestamps in seconds (assumes 30fps if None)
		
		Returns:
			Array of vertical velocities [N-1]
		"""
		if len(ball_positions) < 2:
			return np.array([])

		velocities = []
		for i in range(len(ball_positions) - 1):
			pos_curr = ball_positions[i]
			pos_next = ball_positions[i + 1]

			if timestamps:
				dt = timestamps[i + 1] - timestamps[i]
			else:
				dt = 1.0 / 30.0  # Assume 30fps

			if dt > 0:
				# Vertical velocity (Y component)
				vy = (pos_next[1] - pos_curr[1]) / dt
				velocities.append(vy)
			else:
				velocities.append(0.0)

		return np.array(velocities)

	def compute_knee_flexion(
		self,
		hip_positions: List[np.ndarray],
		knee_positions: List[np.ndarray],
		ankle_positions: List[np.ndarray],
	) -> np.ndarray:
		"""
		Compute knee flexion angles for each frame.
		
		Args:
			hip_positions: List of 3D hip positions
			knee_positions: List of 3D knee positions
			ankle_positions: List of 3D ankle positions
		
		Returns:
			Array of knee flexion angles [N]
		"""
		from ..metrics.biomechanics import joint_angle

		angles = []
		for i in range(len(knee_positions)):
			if i < len(hip_positions) and i < len(ankle_positions):
				angle = joint_angle(hip_positions[i], knee_positions[i], ankle_positions[i])
				angles.append(angle)
			else:
				angles.append(180.0)  # Extended

		return np.array(angles)

	def detect_release_frame(
		self,
		ball_velocities: np.ndarray,
		ball_positions: Optional[List[np.ndarray]] = None,
	) -> Optional[int]:
		"""
		Detect ball release frame based on vertical velocity.
		
		Release occurs when ball velocity becomes positive and exceeds threshold.
		
		Args:
			ball_velocities: Array of ball vertical velocities
			ball_positions: Optional ball positions for validation
		
		Returns:
			Frame index of release or None
		"""
		if len(ball_velocities) == 0:
			return None

		# Find first frame where velocity exceeds threshold
		for i, vel in enumerate(ball_velocities):
			if vel > self.ball_velocity_threshold:
				# Check if ball is still in hand region (optional validation)
				if ball_positions and i < len(ball_positions):
					# Could add validation here (e.g., ball near wrist)
					pass
				return i

		return None

	def detect_crouch_phase(
		self,
		knee_angles: np.ndarray,
		start_frame: int = 0,
		end_frame: Optional[int] = None,
	) -> Optional[Tuple[int, int]]:
		"""
		Detect crouch phase based on knee flexion.
		
		Crouch occurs when knee flexion exceeds threshold.
		
		Args:
			knee_angles: Array of knee flexion angles
			start_frame: Starting frame to search
			end_frame: Ending frame to search (None = end)
		
		Returns:
			(start_frame, end_frame) of crouch phase or None
		"""
		if end_frame is None:
			end_frame = len(knee_angles)

		crouch_start = None
		crouch_end = None

		for i in range(start_frame, end_frame):
			if knee_angles[i] < self.knee_flexion_threshold:  # Flexed = smaller angle
				if crouch_start is None:
					crouch_start = i
				crouch_end = i
			else:
				# End of crouch if we had one
				if crouch_start is not None and crouch_end is not None:
					if crouch_end - crouch_start >= self.min_phase_frames:
						return (crouch_start, crouch_end)

		# Return if we found a valid crouch
		if crouch_start is not None and crouch_end is not None:
			if crouch_end - crouch_start >= self.min_phase_frames:
				return (crouch_start, crouch_end)

		return None

	def detect_phases(
		self,
		pose_results: List[Dict[str, any]],
		ball_trajectory: Optional[List[np.ndarray]] = None,
		ball_timestamps: Optional[List[float]] = None,
	) -> List[Dict[str, any]]:
		"""
		Detect all shooting phases from pose and ball data.
		
		Args:
			pose_results: List of pose detection results with landmarks
			ball_trajectory: Optional list of 3D ball positions
			ball_timestamps: Optional timestamps for ball positions
		
		Returns:
			List of phase detections: [{
				'phase': ShootingPhase,
				'start_frame': int,
				'end_frame': int,
				'confidence': float
			}]
		"""
		phases = []
		total_frames = len(pose_results)

		if total_frames == 0:
			return phases

		# Extract joint positions
		hip_positions = []
		knee_positions = []
		ankle_positions = []

		for result in pose_results:
			landmarks = result.get("landmarks")
			if landmarks is None:
				continue

			# Get right side joints (assuming right-handed shot)
			# MediaPipe indices: right_hip=24, right_knee=26, right_ankle=28
			if len(landmarks) > 28:
				hip_positions.append(landmarks[24])
				knee_positions.append(landmarks[26])
				ankle_positions.append(landmarks[28])
			else:
				hip_positions.append(np.array([0, 0, 0]))
				knee_positions.append(np.array([0, 0, 0]))
				ankle_positions.append(np.array([0, 0, 0]))

		# Compute knee flexion
		knee_angles = self.compute_knee_flexion(hip_positions, knee_positions, ankle_positions)

		# Detect crouch phase (before release)
		crouch_phase = self.detect_crouch_phase(knee_angles, 0, total_frames)
		if crouch_phase:
			phases.append({
				"phase": ShootingPhase.CROUCH,
				"start_frame": crouch_phase[0],
				"end_frame": crouch_phase[1],
				"confidence": 0.8,
			})

		# Detect stance phase (before crouch)
		if crouch_phase:
			if crouch_phase[0] > self.min_phase_frames:
				phases.append({
					"phase": ShootingPhase.STANCE,
					"start_frame": 0,
					"end_frame": crouch_phase[0],
					"confidence": 0.7,
				})
		else:
			# No crouch detected, entire pre-release is stance
			release_frame = total_frames // 2  # Fallback estimate
			phases.append({
				"phase": ShootingPhase.STANCE,
				"start_frame": 0,
				"end_frame": release_frame,
				"confidence": 0.5,
			})

		# Detect release phase (using ball trajectory if available)
		release_frame = None
		if ball_trajectory and len(ball_trajectory) >= 2:
			ball_velocities = self.compute_ball_velocity(ball_trajectory, ball_timestamps)
			release_frame = self.detect_release_frame(ball_velocities, ball_trajectory)
			if release_frame is not None:
				# Release phase is short (few frames around release)
				release_start = max(0, release_frame - 2)
				release_end = min(total_frames, release_frame + 2)
				phases.append({
					"phase": ShootingPhase.RELEASE,
					"start_frame": release_start,
					"end_frame": release_end,
					"confidence": 0.9,
				})
		else:
			# Estimate release frame from pose (when arm is extended upward)
			# Find frame where wrist is highest (arm extension)
			wrist_heights = []
			for result in pose_results:
				landmarks = result.get("landmarks")
				if landmarks is not None and len(landmarks) > 16:
					# Right wrist Y coordinate (lower Y = higher in image for normalized coords)
					wrist_y = landmarks[16][1] if len(landmarks[16]) > 1 else 0.5
					wrist_heights.append(wrist_y)
				else:
					wrist_heights.append(0.5)  # Default middle
			
			if wrist_heights:
				# Find minimum Y (highest wrist position) - this is likely release
				min_wrist_y = min(wrist_heights)
				release_frame = wrist_heights.index(min_wrist_y)
			else:
				# Fallback to midpoint
				release_frame = total_frames // 2
			
			# Release phase is short (few frames around release)
			release_start = max(0, release_frame - 2)
			release_end = min(total_frames - 1, release_frame + 2)
			phases.append({
				"phase": ShootingPhase.RELEASE,
				"start_frame": release_start,
				"end_frame": release_end,
				"confidence": 0.6,  # Moderate confidence for pose-based estimate
			})

		# Detect landing phase (after release)
		# Get release_frame from phases if not set
		if release_frame is None:
			for phase_info in phases:
				if phase_info["phase"] == ShootingPhase.RELEASE:
					release_frame = phase_info["start_frame"] + (phase_info["end_frame"] - phase_info["start_frame"]) // 2
					break
		
		if release_frame is not None:
			landing_start = release_frame + 3
			if landing_start < total_frames:
				phases.append({
					"phase": ShootingPhase.LANDING,
					"start_frame": landing_start,
					"end_frame": total_frames - 1,
					"confidence": 0.6,
				})

		# Sort phases by start_frame
		phases.sort(key=lambda x: x["start_frame"])

		return phases

	def get_phase_at_frame(
		self,
		phases: List[Dict[str, any]],
		frame_idx: int,
	) -> ShootingPhase:
		"""
		Get the phase active at a given frame.
		
		Args:
			phases: List of detected phases
			frame_idx: Frame index to query
		
		Returns:
			Active ShootingPhase or UNKNOWN
		"""
		for phase_info in phases:
			if phase_info["start_frame"] <= frame_idx <= phase_info["end_frame"]:
				return phase_info["phase"]

		return ShootingPhase.UNKNOWN
