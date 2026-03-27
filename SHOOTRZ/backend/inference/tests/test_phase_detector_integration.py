"""
Integration test to ensure PhaseDetector works when imported from router context.

Validates:
- PhaseDetector import succeeds (no relative import errors)
- detect_phases returns motion-based phases on synthetic data
"""

import numpy as np

from inference.phase_detector import PhaseDetector, ShootingPhase


def make_pose_frame(hip_y: float, knee_angle: float, wrist_y: float) -> dict:
	"""
	Create a synthetic pose frame with required landmarks.
	Indexes follow MediaPipe:
	- 24: right_hip
	- 26: right_knee
	- 28: right_ankle
	- 12: right_shoulder
	- 14: right_elbow
	- 16: right_wrist
	"""
	landmarks = np.zeros((33, 3), dtype=float)
	# Hip, knee, ankle positions (simplified vertical offsets)
	landmarks[24] = [0.5, hip_y, 0.0]
	landmarks[26] = [0.5, hip_y + 0.12, 0.0]
	landmarks[28] = [0.5, hip_y + 0.24, 0.0]
	# Shoulder/elbow/wrist (simplified)
	landmarks[12] = [0.5, 0.5, 0.0]
	landmarks[14] = [0.5, 0.55, 0.0]
	landmarks[16] = [0.5, wrist_y, 0.0]

	confidence = np.ones((33,), dtype=float) * 0.9
	return {"landmarks": landmarks, "confidence": confidence, "frame_idx": 0}


def make_sequence() -> list:
	"""Create a simple stance->crouch->release->landing sequence."""
	frames = []
	# STANCE: 0-9
	for _ in range(10):
		frames.append(make_pose_frame(hip_y=0.65, knee_angle=175, wrist_y=0.7))
	# CROUCH: 10-19 (deepest knee bend around frame 15)
	for i in range(10):
		progress = i / 9.0
		hip_y = 0.65 + 0.12 * progress  # hip goes down
		# knee angle decreases to ~120 then starts extending
		knee_angle = 175 - 55 * progress
		wrist_y = 0.7 - 0.05 * progress
		frames.append(make_pose_frame(hip_y=hip_y, knee_angle=knee_angle, wrist_y=wrist_y))
	# RELEASE: 20-24 (wrist flick up)
	for i in range(5):
		progress = i / 4.0
		hip_y = 0.65
		knee_angle = 175
		wrist_y = 0.6 - 0.4 * progress  # rising wrist
		frames.append(make_pose_frame(hip_y=hip_y, knee_angle=knee_angle, wrist_y=wrist_y))
	# LANDING: 25-34 (descending, knees flex a bit)
	for i in range(10):
		progress = i / 9.0
		hip_y = 0.65 + 0.08 * progress  # coming down
		knee_angle = 175 - 25 * progress  # slight flex
		wrist_y = 0.2 + 0.3 * progress
		frames.append(make_pose_frame(hip_y=hip_y, knee_angle=knee_angle, wrist_y=wrist_y))
	return frames


def test_phase_detector_integration():
	"""Ensure PhaseDetector runs end-to-end and produces phases."""
	pose_results = make_sequence()
	detector = PhaseDetector(fps=30.0)
	phases = detector.detect_phases(pose_results)

	assert len(phases) >= 3, "Should detect multiple phases"
	phase_names = [p["phase"] for p in phases]
	assert ShootingPhase.STANCE in phase_names or ShootingPhase.CROUCH in phase_names
	assert ShootingPhase.RELEASE in phase_names
	assert ShootingPhase.LANDING in phase_names

	# Ensure we are not using old format
	assert "start" not in [str(p["phase"]) for p in phases], "Old 'start' phase detected"
