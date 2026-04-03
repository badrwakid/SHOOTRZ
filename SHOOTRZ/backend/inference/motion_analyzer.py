"""
Motion analysis module for basketball shooting motion.

Computes biomechanical signals from pose data:
- Hip vertical velocity
- Knee flexion angles
- Wrist position and velocity
- Local minima/maxima detection
- Arm extension angles
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
	# Savitzky-Golay smoothing for better peak detection (optional)
	from scipy.signal import savgol_filter
	HAS_SAVGOL = True
except Exception:
	HAS_SAVGOL = False


@dataclass
class MotionSignals:
	"""Container for computed motion signals."""
	hip_y: np.ndarray  # Hip vertical positions [N]
	hip_velocity: np.ndarray  # Hip vertical velocity [N-1]
	knee_angles: np.ndarray  # Knee flexion angles [N]
	wrist_y: np.ndarray  # Wrist vertical positions [N]
	wrist_velocity: np.ndarray  # Wrist vertical velocity [N-1]
	wrist_acceleration: np.ndarray  # Wrist vertical acceleration [N-2]
	arm_extension: np.ndarray  # Arm extension angles [N]
	total_frames: int
	fps: float


def moving_average(signal: np.ndarray, window_size: int = 5) -> np.ndarray:
	"""
	Apply moving average smoothing to signal.
	
	Args:
		signal: Input signal array
		window_size: Window size for averaging
		
	Returns:
		Smoothed signal (same length as input)
	"""
	if len(signal) < window_size:
		return signal
	
	# Use convolution for efficient moving average
	kernel = np.ones(window_size) / window_size
	smoothed = np.convolve(signal, kernel, mode='same')
	
	# Fix edges (convolution artifacts at boundaries)
	for i in range(window_size // 2):
		smoothed[i] = np.mean(signal[:i + window_size // 2 + 1])
		smoothed[-(i + 1)] = np.mean(signal[-(i + window_size // 2 + 1):])
	
	return smoothed


def _savgol_smooth(signal: np.ndarray, window_length: int = 7, polyorder: int = 2) -> np.ndarray:
	"""
	Apply Savitzky-Golay smoothing if available; fallback to moving average.
	"""
	if not HAS_SAVGOL:
		return moving_average(signal, window_size=window_length)
	if len(signal) < window_length:
		return signal
	# window_length must be odd and <= len(signal)
	if window_length % 2 == 0:
		window_length += 1
	window_length = min(window_length, len(signal) if len(signal) % 2 == 1 else len(signal) - 1)
	if window_length < 3:
		return signal
	try:
		return savgol_filter(signal, window_length=window_length, polyorder=polyorder, mode="interp")
	except Exception:
		return moving_average(signal, window_size=window_length)


def compute_hip_vertical_velocity(
	hip_positions: List[np.ndarray],
	fps: float = 30.0,
	smooth_window: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
	"""
	Compute hip vertical velocity with smoothing.
	
	Args:
		hip_positions: List of hip positions (normalized coordinates)
		fps: Video frames per second
		smooth_window: Window size for smoothing
		
	Returns:
		Tuple of (hip_y positions [N], hip_velocity [N-1])
	"""
	if len(hip_positions) < 2:
		return np.array([]), np.array([])
	
	# Extract Y coordinates (vertical position)
	hip_y = np.array([pos[1] if len(pos) > 1 else 0.5 for pos in hip_positions])
	
	# Apply smoothing to positions first
	hip_y_smooth = moving_average(hip_y, window_size=smooth_window)
	
	# Compute velocity (change in position per frame)
	hip_velocity = np.diff(hip_y_smooth) * fps
	
	# Apply additional smoothing to velocity
	if len(hip_velocity) >= smooth_window:
		hip_velocity = moving_average(hip_velocity, window_size=smooth_window)
	
	return hip_y_smooth, hip_velocity


def compute_knee_angles(
	hip_positions: List[np.ndarray],
	knee_positions: List[np.ndarray],
	ankle_positions: List[np.ndarray],
	smooth_window: int = 3,
) -> np.ndarray:
	"""
	Compute knee flexion angles with smoothing.
	
	Args:
		hip_positions: List of hip positions
		knee_positions: List of knee positions
		ankle_positions: List of ankle positions
		smooth_window: Window size for smoothing
		
	Returns:
		Array of knee angles in degrees [N]
	"""
	from metrics.biomechanics import joint_angle
	
	angles = []
	min_len = min(len(hip_positions), len(knee_positions), len(ankle_positions))
	
	for i in range(min_len):
		hip = np.array(hip_positions[i][:3]) if len(hip_positions[i]) >= 3 else np.append(hip_positions[i][:2], [0.0])
		knee = np.array(knee_positions[i][:3]) if len(knee_positions[i]) >= 3 else np.append(knee_positions[i][:2], [0.0])
		ankle = np.array(ankle_positions[i][:3]) if len(ankle_positions[i]) >= 3 else np.append(ankle_positions[i][:2], [0.0])
		
		angle = joint_angle(hip, knee, ankle)
		angles.append(angle)
	
	angles = np.array(angles)
	
	# Apply smoothing
	if len(angles) >= smooth_window:
		angles = moving_average(angles, window_size=smooth_window)
	
	return angles


def compute_wrist_velocity(
	wrist_positions: List[np.ndarray],
	fps: float = 30.0,
	smooth_window: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
	"""
	Compute wrist vertical velocity with smoothing.
	
	Args:
		wrist_positions: List of wrist positions (normalized coordinates)
		fps: Video frames per second
		smooth_window: Window size for smoothing
		
	Returns:
		Tuple of (wrist_y positions [N], wrist_velocity [N-1])
	"""
	if len(wrist_positions) < 2:
		return np.array([]), np.array([])
	
	# Extract Y coordinates (vertical position)
	wrist_y = np.array([pos[1] if len(pos) > 1 else 0.5 for pos in wrist_positions])
	
	# Apply smoothing to positions first
	wrist_y_smooth = moving_average(wrist_y, window_size=smooth_window)
	
	# Compute velocity (change in position per frame)
	wrist_velocity = np.diff(wrist_y_smooth) * fps
	
	# Apply additional smoothing to velocity
	if len(wrist_velocity) >= smooth_window:
		wrist_velocity = moving_average(wrist_velocity, window_size=smooth_window)
	
	return wrist_y_smooth, wrist_velocity


def compute_wrist_acceleration(
	wrist_velocity: np.ndarray,
	fps: float = 30.0,
	smooth_window: int = 5,
) -> np.ndarray:
	"""
	Compute wrist vertical acceleration with smoothing.

	Args:
		wrist_velocity: Wrist vertical velocities [N-1]
		fps: Video frames per second
		smooth_window: Window size for smoothing

	Returns:
		Array of wrist accelerations [N-2]
	"""
	if len(wrist_velocity) < 2:
		return np.array([])

	# Apply smoothing before differentiating to reduce noise
	vel_smooth = _savgol_smooth(wrist_velocity, window_length=max(5, smooth_window | 1), polyorder=2)

	accel = np.diff(vel_smooth) * fps

	# Smooth acceleration as well
	if len(accel) >= smooth_window:
		accel = _savgol_smooth(accel, window_length=max(5, smooth_window | 1), polyorder=2)

	return accel


def compute_arm_extension(
	shoulder_positions: List[np.ndarray],
	elbow_positions: List[np.ndarray],
	wrist_positions: List[np.ndarray],
	smooth_window: int = 3,
) -> np.ndarray:
	"""
	Compute arm extension angles (shoulder-elbow-wrist).
	
	Args:
		shoulder_positions: List of shoulder positions
		elbow_positions: List of elbow positions
		wrist_positions: List of wrist positions
		smooth_window: Window size for smoothing
		
	Returns:
		Array of arm extension angles in degrees [N]
	"""
	from metrics.biomechanics import joint_angle
	
	angles = []
	min_len = min(len(shoulder_positions), len(elbow_positions), len(wrist_positions))
	
	for i in range(min_len):
		shoulder = np.array(shoulder_positions[i][:3]) if len(shoulder_positions[i]) >= 3 else np.append(shoulder_positions[i][:2], [0.0])
		elbow = np.array(elbow_positions[i][:3]) if len(elbow_positions[i]) >= 3 else np.append(elbow_positions[i][:2], [0.0])
		wrist = np.array(wrist_positions[i][:3]) if len(wrist_positions[i]) >= 3 else np.append(wrist_positions[i][:2], [0.0])
		
		angle = joint_angle(shoulder, elbow, wrist)
		angles.append(angle)
	
	angles = np.array(angles)
	
	# Apply smoothing
	if len(angles) >= smooth_window:
		angles = moving_average(angles, window_size=smooth_window)
	
	return angles


def detect_local_minima(
	signal: np.ndarray,
	window_size: int = 5,
	min_prominence: Optional[float] = None,
) -> List[int]:
	"""
	Detect local minima in signal.
	
	Args:
		signal: Input signal array
		window_size: Window size for local comparison
		min_prominence: Minimum prominence (depth) of minima
		
	Returns:
		List of frame indices where local minima occur
	"""
	if len(signal) < window_size:
		return []
	
	minima = []
	half_window = window_size // 2
	
	for i in range(half_window, len(signal) - half_window):
		# Check if this is a local minimum
		window = signal[i - half_window : i + half_window + 1]
		if signal[i] == np.min(window):
			# Check prominence if specified
			if min_prominence is not None:
				left_max = np.max(signal[max(0, i - window_size * 2) : i])
				right_max = np.max(signal[i : min(len(signal), i + window_size * 2)])
				prominence = min(left_max - signal[i], right_max - signal[i])
				
				if prominence >= min_prominence:
					minima.append(i)
			else:
				minima.append(i)
	
	return minima


def detect_local_maxima(
	signal: np.ndarray,
	window_size: int = 5,
	min_prominence: Optional[float] = None,
) -> List[int]:
	"""
	Detect local maxima in signal.
	
	Args:
		signal: Input signal array
		window_size: Window size for local comparison
		min_prominence: Minimum prominence (height) of maxima
		
	Returns:
		List of frame indices where local maxima occur
	"""
	if len(signal) < window_size:
		return []
	
	maxima = []
	half_window = window_size // 2
	
	for i in range(half_window, len(signal) - half_window):
		# Check if this is a local maximum
		window = signal[i - half_window : i + half_window + 1]
		if signal[i] == np.max(window):
			# Check prominence if specified
			if min_prominence is not None:
				left_min = np.min(signal[max(0, i - window_size * 2) : i])
				right_min = np.min(signal[i : min(len(signal), i + window_size * 2)])
				prominence = min(signal[i] - left_min, signal[i] - right_min)
				
				if prominence >= min_prominence:
					maxima.append(i)
			else:
				maxima.append(i)
	
	return maxima


def analyze_motion_patterns(
	pose_results: List[Dict[str, Any]],
	fps: float = 30.0,
) -> MotionSignals:
	"""
	Analyze motion patterns from pose results.
	
	Extracts and computes all motion signals needed for phase detection.
	
	Args:
		pose_results: List of pose detection results with landmarks
		fps: Video frames per second
		
	Returns:
		MotionSignals object containing all computed signals
	"""
	# Extract joint positions
	hip_positions = []
	knee_positions = []
	ankle_positions = []
	shoulder_positions = []
	elbow_positions = []
	wrist_positions = []
	
	for result in pose_results:
		landmarks = result.get("landmarks")
		if landmarks is None or len(landmarks) < 29:
			# Use default positions if landmarks missing
			hip_positions.append(np.array([0.5, 0.5, 0.0]))
			knee_positions.append(np.array([0.5, 0.5, 0.0]))
			ankle_positions.append(np.array([0.5, 0.5, 0.0]))
			shoulder_positions.append(np.array([0.5, 0.5, 0.0]))
			elbow_positions.append(np.array([0.5, 0.5, 0.0]))
			wrist_positions.append(np.array([0.5, 0.5, 0.0]))
			continue
		
		# MediaPipe pose indices
		# Right side (assuming right-handed shot)
		hip_positions.append(landmarks[24])  # right_hip
		knee_positions.append(landmarks[26])  # right_knee
		ankle_positions.append(landmarks[28])  # right_ankle
		shoulder_positions.append(landmarks[12])  # right_shoulder
		elbow_positions.append(landmarks[14])  # right_elbow
		wrist_positions.append(landmarks[16])  # right_wrist
	
	# Compute all signals
	hip_y, hip_velocity = compute_hip_vertical_velocity(hip_positions, fps)
	knee_angles = compute_knee_angles(hip_positions, knee_positions, ankle_positions)
	wrist_y, wrist_velocity = compute_wrist_velocity(wrist_positions, fps)
	wrist_acceleration = compute_wrist_acceleration(wrist_velocity, fps)
	arm_extension = compute_arm_extension(shoulder_positions, elbow_positions, wrist_positions)
	
	return MotionSignals(
		hip_y=hip_y,
		hip_velocity=hip_velocity,
		knee_angles=knee_angles,
		wrist_y=wrist_y,
		wrist_velocity=wrist_velocity,
		wrist_acceleration=wrist_acceleration,
		arm_extension=arm_extension,
		total_frames=len(pose_results),
		fps=fps,
	)


def detect_velocity_zero_crossings(
	velocity: np.ndarray,
	direction: str = 'positive',
) -> List[int]:
	"""
	Detect zero crossings in velocity signal.
	
	Args:
		velocity: Velocity signal
		direction: 'positive' for negative->positive, 'negative' for positive->negative
		
	Returns:
		List of frame indices where crossings occur
	"""
	crossings = []
	
	for i in range(len(velocity) - 1):
		if direction == 'positive':
			# Crossing from negative to positive (ascending)
			if velocity[i] <= 0 and velocity[i + 1] > 0:
				crossings.append(i + 1)
		elif direction == 'negative':
			# Crossing from positive to negative (descending)
			if velocity[i] >= 0 and velocity[i + 1] < 0:
				crossings.append(i + 1)
	
	return crossings

