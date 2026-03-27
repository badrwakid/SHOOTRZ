"""
Phase detection state machine for basketball shooting motion.

Motion-based detection system that identifies:
- STANCE → CROUCH → RELEASE → LANDING phases
- Handles videos that start mid-motion (e.g., already in crouch)
- Uses adaptive thresholds and multi-signal fusion
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from scipy.signal import find_peaks, savgol_filter

from inference.motion_analyzer import (
	analyze_motion_patterns,
	MotionSignals,
	detect_local_minima,
	detect_local_maxima,
	detect_velocity_zero_crossings,
)
from scipy.signal import find_peaks


class ShootingPhase(Enum):
	"""Shooting motion phases."""
	STANCE = "stance"
	CROUCH = "crouch"
	RELEASE = "release"
	LANDING = "landing"
	UNKNOWN = "unknown"


class InitialState(Enum):
	"""Initial state when video starts."""
	IN_STANCE = "in_stance"
	IN_CROUCH = "in_crouch"
	IN_CROUCH_ASCENT = "in_crouch_ascent"
	IN_RELEASE = "in_release"
	UNKNOWN = "unknown"


@dataclass
class AdaptiveThresholds:
	"""Adaptive thresholds calculated per video."""
	knee_crouch_threshold: float  # Knee angle below which = crouch
	hip_descent_threshold: float  # Hip drop indicating crouch start
	wrist_peak_threshold: float  # Wrist height for release
	min_crouch_depth: float  # Minimum hip drop for valid crouch


@dataclass
class PhaseInfo:
	"""Information about a detected phase."""
	phase: ShootingPhase
	start_frame: int
	end_frame: int
	confidence: float
	peak_frame: Optional[int] = None  # Key frame within phase


class PhaseDetector:
	"""
	Motion-based phase detection system.
	
	Uses multi-signal fusion and adaptive thresholds to accurately detect
	shooting phases, handling edge cases like videos starting mid-motion.
	"""

	def __init__(
		self,
		fps: float = 30.0,
		min_phase_frames: int = 3,
	):
		"""
		Initialize phase detector.
		
		Args:
			fps: Video frames per second
			min_phase_frames: Minimum frames required for a phase
		"""
		self.fps = fps
		self.min_phase_frames = min_phase_frames

	def _calculate_adaptive_thresholds(
		self,
		motion_signals: MotionSignals,
	) -> AdaptiveThresholds:
		"""
		Calculate adaptive thresholds based on video motion range.
		
		Args:
			motion_signals: Computed motion signals
			
		Returns:
			AdaptiveThresholds object
		"""
		# Knee angle range
		knee_min = np.min(motion_signals.knee_angles)
		knee_max = np.max(motion_signals.knee_angles)
		knee_range = knee_max - knee_min
		
		# Crouch threshold: 30% from minimum (most flexed)
		knee_crouch_threshold = knee_min + 0.3 * knee_range
		
		# Hip height range
		hip_min = np.min(motion_signals.hip_y)
		hip_max = np.max(motion_signals.hip_y)
		hip_range = hip_max - hip_min
		
		# Descent threshold: 10% drop from maximum
		hip_descent_threshold = hip_max - 0.1 * hip_range
		
		# Minimum crouch depth: 15% of total range
		min_crouch_depth = 0.15 * hip_range
		
		# Wrist peak threshold (for release detection)
		wrist_min = np.min(motion_signals.wrist_y)
		wrist_max = np.max(motion_signals.wrist_y)
		wrist_range = wrist_max - wrist_min
		wrist_peak_threshold = wrist_min + 0.2 * wrist_range
		
		return AdaptiveThresholds(
			knee_crouch_threshold=knee_crouch_threshold,
			hip_descent_threshold=hip_descent_threshold,
			wrist_peak_threshold=wrist_peak_threshold,
			min_crouch_depth=min_crouch_depth,
		)

	def _detect_initial_state(
		self,
		motion_signals: MotionSignals,
		first_n_frames: int = 10,
	) -> InitialState:
		"""
		Detect initial state when video starts (critical for mid-motion videos).
		
		Args:
			motion_signals: Computed motion signals
			first_n_frames: Number of initial frames to analyze
			
		Returns:
			Detected initial state
		"""
		if motion_signals.total_frames < first_n_frames:
			first_n_frames = motion_signals.total_frames
		
		if first_n_frames < 3:
			return InitialState.UNKNOWN
		
		# Analyze first N frames
		initial_hip_height = np.mean(motion_signals.hip_y[:first_n_frames])
		initial_knee_angle = np.mean(motion_signals.knee_angles[:first_n_frames])
		
		# Hip velocity (check if ascending/descending)
		if len(motion_signals.hip_velocity) >= first_n_frames:
			initial_hip_velocity = np.mean(motion_signals.hip_velocity[:first_n_frames])
		else:
			initial_hip_velocity = 0.0
		
		# Calculate video-wide ranges for comparison
		hip_range = np.max(motion_signals.hip_y) - np.min(motion_signals.hip_y)
		if hip_range == 0:
			return InitialState.UNKNOWN
		
		hip_percentile = (initial_hip_height - np.min(motion_signals.hip_y)) / hip_range
		
		# Decision logic
		# Check for crouch (low hip + flexed knee)
		if hip_percentile < 0.3 and initial_knee_angle < 150:
			# Hip is low and knee is flexed
			if initial_hip_velocity > 0:
				# Rising from crouch (already past bottom)
				return InitialState.IN_CROUCH_ASCENT
			else:
				# Currently in crouch (descending or at bottom)
				return InitialState.IN_CROUCH
		
		# Check for stance (upright position)
		elif initial_knee_angle > 160 and hip_percentile > 0.7:
			return InitialState.IN_STANCE
		
		# Check for release (wrist high, arm extended)
		if len(motion_signals.wrist_y) >= first_n_frames:
			initial_wrist_height = np.mean(motion_signals.wrist_y[:first_n_frames])
			wrist_range = np.max(motion_signals.wrist_y) - np.min(motion_signals.wrist_y)
			if wrist_range > 0:
				wrist_percentile = (initial_wrist_height - np.min(motion_signals.wrist_y)) / wrist_range
				if wrist_percentile < 0.3 and initial_knee_angle > 150:
					# Wrist is high (low Y) and legs extended
					return InitialState.IN_RELEASE
		
		# Ambiguous
		return InitialState.UNKNOWN

	def _validate_shooting_motion(
		self,
		motion_signals: MotionSignals,
	) -> Tuple[bool, str]:
		"""
		Lightweight shooting motion validator based on wrist dip→rise pattern and duration.

		Checks:
		- Enough frames and wrist data
		- Wrist vertical range exceeds threshold
		- Dip (max Y) happens before rise (min Y)
		- Motion duration reasonable (< 300 frames ~10s at 30fps)
		"""
		total_frames = motion_signals.total_frames
		if total_frames < 10 or len(motion_signals.wrist_y) < 10:
			return False, "insufficient frames"

		wrist_y = motion_signals.wrist_y
		wrist_range = float(np.max(wrist_y) - np.min(wrist_y))

		# Threshold: at least ~5% normalized height range
		if wrist_range < 0.05:
			return False, f"low wrist vertical range ({wrist_range:.3f})"

		# Dip then rise pattern
		max_idx = int(np.argmax(wrist_y))  # dip bottom (hand low, Y high)
		min_idx = int(np.argmin(wrist_y))  # wrist peak (hand high, Y low)
		if max_idx >= min_idx:
			return False, "no dip->rise wrist pattern"

		# Duration sanity check
		if total_frames > 300:
			return False, f"motion too long ({total_frames} frames)"

		return True, "ok"

	def _detect_stance_phase(
		self,
		motion_signals: MotionSignals,
		thresholds: AdaptiveThresholds,
		initial_state: InitialState,
	) -> Optional[PhaseInfo]:
		"""
		Detect stance phase (initial setup position).
		
		Args:
			motion_signals: Computed motion signals
			thresholds: Adaptive thresholds
			initial_state: Detected initial state
			
		Returns:
			PhaseInfo or None if no stance detected
		"""
		# Skip stance if video starts in crouch or later
		if initial_state in [InitialState.IN_CROUCH, InitialState.IN_CROUCH_ASCENT, InitialState.IN_RELEASE]:
			return None
		
		# Find when hip starts descending (crouch begins)
		descent_start = None
		
		# Look for sustained hip descent
		for i in range(len(motion_signals.hip_velocity)):
			if motion_signals.hip_velocity[i] < -0.5:  # Negative = descending
				# Check if descent continues
				if i + 3 < len(motion_signals.hip_velocity):
					next_velocities = motion_signals.hip_velocity[i:i+3]
					if np.mean(next_velocities) < 0:
						descent_start = i
						break
		
		if descent_start is None or descent_start < self.min_phase_frames:
			# No clear crouch detected, stance extends until release
			# Find release start (wrist rising)
			wrist_minima = detect_local_minima(motion_signals.wrist_y, window_size=5)
			if wrist_minima:
				release_approx = wrist_minima[0]
				if release_approx > self.min_phase_frames:
					return PhaseInfo(
						phase=ShootingPhase.STANCE,
						start_frame=0,
						end_frame=release_approx,
						confidence=0.6,
					)
			
			# Fallback: first half of video
			mid_point = motion_signals.total_frames // 2
			if mid_point > self.min_phase_frames:
				return PhaseInfo(
					phase=ShootingPhase.STANCE,
					start_frame=0,
					end_frame=mid_point,
					confidence=0.5,
				)
			return None
		
		# Stance ends when descent begins
		return PhaseInfo(
			phase=ShootingPhase.STANCE,
			start_frame=0,
			end_frame=descent_start,
			confidence=0.7,
		)

	def _detect_crouch_phase(
		self,
		motion_signals: MotionSignals,
		thresholds: AdaptiveThresholds,
		initial_state: InitialState,
		stance_end: Optional[int] = None,
	) -> Optional[PhaseInfo]:
		"""
		Detect crouch phase by combining MAX knee flexion (most bent knees) and
		wrist dip (lowest hand). Uses both signals to anchor the deepest crouch.
		
		Args:
			motion_signals: Computed motion signals
			thresholds: Adaptive thresholds
			initial_state: Detected initial state
			stance_end: End frame of stance phase (if detected)
			
		Returns:
			PhaseInfo or None if no crouch detected
		"""
		# Determine start frame
		if initial_state in [InitialState.IN_CROUCH, InitialState.IN_CROUCH_ASCENT]:
			# Video starts in crouch
			start_frame = 0
		elif stance_end is not None:
			# Start after stance
			start_frame = stance_end
		else:
			# Find descent start
			start_frame = 0
			for i in range(len(motion_signals.hip_velocity)):
				if motion_signals.hip_velocity[i] < -0.3:
					start_frame = i
					break
		
		# Search window
		search_start = max(0, start_frame)
		search_end = min(len(motion_signals.knee_angles), search_start + 120)  # up to ~4s
		
		if search_end - search_start < self.min_phase_frames:
			return None
		
		knee_segment = motion_signals.knee_angles[search_start:search_end]
		wrist_segment = motion_signals.wrist_y[search_start:search_end] if len(motion_signals.wrist_y) >= search_end else []
		if len(knee_segment) < 5:
			return None
		
		# Find absolute minimum knee angle (most flexed = deepest crouch)
		min_knee_idx = np.argmin(knee_segment)
		peak_frame_knee = search_start + int(min_knee_idx)
		min_knee_angle = knee_segment[min_knee_idx]
		
		# Validate it's actually a crouch (knee angle < 150 degrees)
		if min_knee_angle > 150:
			# Not a real crouch, too extended
			return None
		
		# Consider wrist dip (lowest hand) for cross-check
		wrist_peak_frame = None
		if len(wrist_segment) >= 5:
			wrist_maxima = detect_local_maxima(wrist_segment, window_size=5)
			if wrist_maxima:
				wrist_peak_frame = search_start + int(wrist_maxima[0])
			else:
				wrist_peak_frame = search_start + int(np.argmax(wrist_segment))

		# Combined crouch bottom: whichever occurs later (ensure both motions completed)
		peak_frame = peak_frame_knee
		if wrist_peak_frame is not None and wrist_peak_frame > peak_frame_knee:
			peak_frame = wrist_peak_frame

		# Find when crouch starts (descent begins): knee starts flexing OR wrist starts dipping
		crouch_start = start_frame
		for i in range(start_frame, peak_frame):
			if motion_signals.knee_angles[i] < thresholds.knee_crouch_threshold or (
				i < len(motion_signals.wrist_y) and motion_signals.wrist_y[i] > motion_signals.wrist_y[start_frame]
			):
				crouch_start = i
				break

		# Find when crouch ends (ascent begins - knee starts extending OR wrist rises)
		crouch_end = peak_frame
		for i in range(peak_frame, min(len(motion_signals.knee_angles), peak_frame + 45)):
			# Look for knee extension (angle increasing) OR wrist rising
			if i + 3 < len(motion_signals.knee_angles):
				knee_trend = motion_signals.knee_angles[i + 3] - motion_signals.knee_angles[i]
				wrist_trend = 0.0
				if i + 3 < len(motion_signals.wrist_y):
					wrist_trend = motion_signals.wrist_y[i + 3] - motion_signals.wrist_y[i]
				if knee_trend > 5 or wrist_trend < -0.01:  # Knee extending or wrist rising
					crouch_end = i
					break
		
		# Ensure minimum duration
		if crouch_end - crouch_start < self.min_phase_frames:
			crouch_end = crouch_start + self.min_phase_frames
		
		# Confidence: knee flexion depth + wrist dip presence
		max_knee = np.max(motion_signals.knee_angles)
		knee_flexion_range = max_knee - min_knee_angle
		knee_conf = min(1.0, knee_flexion_range / 60.0)
		wrist_conf = 0.8 if wrist_peak_frame is not None else 0.6
		confidence = max(0.5, (knee_conf + wrist_conf) / 2)
		
		return PhaseInfo(
			phase=ShootingPhase.CROUCH,
			start_frame=crouch_start,
			end_frame=crouch_end,
			confidence=confidence,
			peak_frame=peak_frame,
		)

	def _detect_release_phase(
		self,
		motion_signals: MotionSignals,
		thresholds: AdaptiveThresholds,
		previous_phase_end: int,
		ball_trajectory: Optional[List[np.ndarray]] = None,
	) -> Optional[PhaseInfo]:
		"""
		Detect release phase - the EXACT wrist flick in the air.
		
		Uses multi-signal fusion with emphasis on wrist acceleration and velocity
		zero-crossing to pinpoint the flick moment.
		
		Args:
			motion_signals: Computed motion signals
			thresholds: Adaptive thresholds
			previous_phase_end: End frame of previous phase
			ball_trajectory: Optional ball trajectory
			
		Returns:
			PhaseInfo or None if no release detected
		"""
		search_start = max(0, previous_phase_end)
		search_end = motion_signals.total_frames
		
		# CRITICAL: Detect the wrist FLICK moment
		# The wrist flick creates a sharp velocity change
		
		if len(motion_signals.wrist_velocity) <= search_start:
			return None
		
		wrist_vel_segment = motion_signals.wrist_velocity[search_start:search_end]
		wrist_y_segment = motion_signals.wrist_y[search_start:search_end]
		wrist_accel_segment = motion_signals.wrist_acceleration[search_start:search_end] if len(motion_signals.wrist_acceleration) > search_start else np.array([])
		
		if len(wrist_vel_segment) < 5:
			return None
		
		candidates = []

		# Signal 1: Wrist acceleration peak (flick snap)
		if len(wrist_accel_segment) >= 5:
			# Look for strong negative acceleration (snap downward after lift)
			peaks, props = find_peaks(-wrist_accel_segment, prominence=0.5)
			if len(peaks) > 0:
				best_idx = int(np.argmax(props.get("prominences", np.ones_like(peaks))))
				accel_frame = search_start + int(peaks[best_idx])
				accel_conf = 0.95
				candidates.append((accel_frame, accel_conf, 0.5))

		# Signal 2: Velocity zero-crossing (upward to downward)
		zero_crossings = detect_velocity_zero_crossings(wrist_vel_segment, direction='negative')
		if zero_crossings:
			vel_frame = search_start + zero_crossings[0]
			vel_conf = 0.9
			candidates.append((vel_frame, vel_conf, 0.3))

		# Signal 3: Wrist height peak (highest point)
		wrist_minima = detect_local_minima(wrist_y_segment, window_size=5)
		if wrist_minima:
			height_frame = search_start + int(wrist_minima[0])
			height_conf = 0.7
		else:
			height_frame = search_start + int(np.argmin(wrist_y_segment))
			height_conf = 0.6
		candidates.append((height_frame, height_conf, 0.2))

		# Choose weighted best frame
		if not candidates:
			return None
		total_weight = sum(w for _, c, w in candidates if c > 0.5)
		if total_weight == 0:
			release_frame = int(np.mean([f for f, _, _ in candidates]))
			confidence = 0.5
		else:
			weighted_frame = sum(f * c * w for f, c, w in candidates if c > 0.5) / total_weight
			release_frame = int(weighted_frame)
			confidence = sum(c * w for _, c, w in candidates) / sum(w for _, _, w in candidates)
		
		# Validate player is in the air (knees should be relatively extended)
		if release_frame < len(motion_signals.knee_angles):
			knee_at_release = motion_signals.knee_angles[release_frame]
			# If knees are very flexed at "release", might not be airborne
			if knee_at_release < 140:
				# Adjust confidence down
				confidence *= 0.7
		
		# Additional validation: Arm should be extended at release
		if release_frame < len(motion_signals.arm_extension):
			arm_at_release = motion_signals.arm_extension[release_frame]
			if arm_at_release > 150:  # Well extended
				confidence = min(1.0, confidence * 1.1)
		
		# Release is a very short moment (1-3 frames around the flick)
		start_frame = max(search_start, release_frame - 1)
		end_frame = min(search_end - 1, release_frame + 2)
		
		if end_frame - start_frame < 1:
			end_frame = start_frame + 1
		
		return PhaseInfo(
			phase=ShootingPhase.RELEASE,
			start_frame=start_frame,
			end_frame=end_frame,
			confidence=confidence,
			peak_frame=release_frame,  # Exact flick moment
		)

	def _detect_landing_phase(
		self,
		motion_signals: MotionSignals,
		release_end: int,
	) -> Optional[PhaseInfo]:
		"""
		Detect landing phase - when feet touch the ground after release.
		
		Landing is detected by:
		1. Hip descending (Y increasing, moving down)
		2. Knee flexion increasing (absorbing impact)
		3. Velocity changes indicating ground contact
		
		Args:
			motion_signals: Computed motion signals
			release_end: End frame of release phase
			
		Returns:
			PhaseInfo or None if no landing detected
		"""
		search_start = release_end + 1
		search_end = motion_signals.total_frames - 1
		
		if search_end - search_start < self.min_phase_frames:
			return None
		
		# Try to detect the exact landing moment (feet touching ground)
		landing_frame = None
		
		# Method 1: Find when hip starts descending (falling back down)
		if search_start < len(motion_signals.hip_velocity):
			hip_vel_segment = motion_signals.hip_velocity[search_start:search_end]
			
			# Look for positive hip velocity (moving down = Y increasing)
			for i, vel in enumerate(hip_vel_segment):
				if vel > 0.3:  # Descending
					# Check for sustained descent (landing impact)
					if i + 2 < len(hip_vel_segment):
						next_vels = hip_vel_segment[i:i+3]
						if np.mean(next_vels) > 0:
							landing_frame = search_start + i
							break
		
		# Method 2: Find when knees start flexing again (absorbing landing impact)
		if landing_frame is None and search_start < len(motion_signals.knee_angles):
			knee_segment = motion_signals.knee_angles[search_start:search_end]
			
			# After release, knees should start at relatively extended
			# Then flex again on landing
			if len(knee_segment) > 5:
				# Look for knee flexion (angle decreasing)
				for i in range(len(knee_segment) - 3):
					knee_change = knee_segment[i+3] - knee_segment[i]
					if knee_change < -5:  # Knees flexing (decreasing angle)
						landing_frame = search_start + i
						break
		
		# If we found a specific landing moment
		if landing_frame is not None:
			confidence = 0.75
			# Landing phase extends from landing moment to end of video
			return PhaseInfo(
				phase=ShootingPhase.LANDING,
				start_frame=landing_frame,
				end_frame=search_end,
				confidence=confidence,
				peak_frame=landing_frame,  # Exact ground contact moment
			)
		
		# Fallback: Landing starts right after release
		return PhaseInfo(
			phase=ShootingPhase.LANDING,
			start_frame=search_start,
			end_frame=search_end,
			confidence=0.5,
		)

	def _validate_phase_sequence(
		self,
		phases: List[PhaseInfo],
	) -> List[PhaseInfo]:
		"""
		Validate and fix phase sequence to ensure temporal consistency.
		
		Args:
			phases: List of detected phases
			
		Returns:
			Validated phase list
		"""
		if not phases:
			return phases
		
		# Sort by start frame
		phases = sorted(phases, key=lambda p: p.start_frame)
		
		# Ensure no overlaps
		for i in range(len(phases) - 1):
			if phases[i].end_frame >= phases[i + 1].start_frame:
				# Overlap detected, adjust boundary
				boundary = (phases[i].end_frame + phases[i + 1].start_frame) // 2
				phases[i].end_frame = boundary
				phases[i + 1].start_frame = boundary + 1
		
		# Ensure minimum duration
		validated = []
		for phase in phases:
			if phase.end_frame - phase.start_frame >= self.min_phase_frames - 1:
				validated.append(phase)
		
		return validated

	def detect_phases(
		self,
		pose_results: List[Dict[str, Any]],
		ball_trajectory: Optional[List[np.ndarray]] = None,
		ball_timestamps: Optional[List[float]] = None,
	) -> List[Dict[str, Any]]:
		"""
		Detect all shooting phases using motion-based analysis.
		
		Args:
			pose_results: List of pose detection results with landmarks
			ball_trajectory: Optional list of 3D ball positions
			ball_timestamps: Optional timestamps for ball positions
			
		Returns:
			List of phase detections: [{
				'phase': ShootingPhase,
				'start_frame': int,
				'end_frame': int,
				'confidence': float,
				'peak_frame': Optional[int]
			}]
		"""
		if len(pose_results) == 0:
			return []
		
		# Step 1: Analyze motion patterns
		motion_signals = analyze_motion_patterns(pose_results, self.fps)

		# Step 1b: Validate motion pattern to ensure this looks like a shot
		is_valid, reason = self._validate_shooting_motion(motion_signals)
		if not is_valid:
			# Return empty to let caller decide fallback
			return []
		
		# Step 2: Calculate adaptive thresholds
		thresholds = self._calculate_adaptive_thresholds(motion_signals)
		
		# Step 3: Detect initial state (critical for mid-motion videos)
		initial_state = self._detect_initial_state(motion_signals)
		
		# Step 4: Detect individual phases
		detected_phases: List[PhaseInfo] = []
		
		# Detect stance
		stance = self._detect_stance_phase(motion_signals, thresholds, initial_state)
		if stance:
			detected_phases.append(stance)
		
		# Detect crouch
		stance_end = stance.end_frame if stance else None
		crouch = self._detect_crouch_phase(motion_signals, thresholds, initial_state, stance_end)
		if crouch:
			detected_phases.append(crouch)
		
		# Detect release
		previous_end = crouch.end_frame if crouch else (stance.end_frame if stance else 0)
		release = self._detect_release_phase(motion_signals, thresholds, previous_end, ball_trajectory)
		if release:
			detected_phases.append(release)
		
		# Detect landing
		if release:
			landing = self._detect_landing_phase(motion_signals, release.end_frame)
			if landing:
				detected_phases.append(landing)
		
		# Step 5: Validate sequence
		validated_phases = self._validate_phase_sequence(detected_phases)
		
		# Convert to dict format
		result = []
		for phase_info in validated_phases:
			phase_dict = {
				"phase": phase_info.phase,
				"start_frame": phase_info.start_frame,
				"end_frame": phase_info.end_frame,
				"confidence": phase_info.confidence,
			}
			if phase_info.peak_frame is not None:
				phase_dict["peak_frame"] = phase_info.peak_frame
			result.append(phase_dict)
		
		return result

	def get_phase_for_each_frame(
		self,
		pose_results: List[Dict[str, Any]],
		ball_trajectory: Optional[List[np.ndarray]] = None,
	) -> List[ShootingPhase]:
		"""
		Get phase assignment for every frame in the video.
		
		Args:
			pose_results: List of pose detection results
			ball_trajectory: Optional ball trajectory
			
		Returns:
			List of ShootingPhase for each frame [N]
		"""
		total_frames = len(pose_results)
		phases = self.detect_phases(pose_results, ball_trajectory)
		
		# Initialize all frames as UNKNOWN
		frame_phases = [ShootingPhase.UNKNOWN] * total_frames
		
		# Assign phases to frames
		for phase_info in phases:
			phase = phase_info["phase"]
			start = phase_info["start_frame"]
			end = phase_info["end_frame"]
			
			for frame_idx in range(start, min(end + 1, total_frames)):
				frame_phases[frame_idx] = phase
		
		return frame_phases

	def get_phase_at_frame(
		self,
		phases: List[Dict[str, Any]],
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
