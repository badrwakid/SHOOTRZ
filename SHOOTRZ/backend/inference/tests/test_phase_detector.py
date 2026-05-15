"""
Comprehensive tests for phase detection system.

Tests cover:
- Standard shots (STANCE → CROUCH → RELEASE → LANDING)
- Quick release shots (no crouch)
- Videos starting mid-crouch (CRITICAL)
- Videos starting during crouch ascent
- Partial videos
- Low quality pose detection
"""

import numpy as np
import pytest
from typing import List, Dict, Any

from ..phase_detector import (
	PhaseDetector,
	ShootingPhase,
	InitialState,
)


def create_mock_pose_result(
	hip_y: float,
	knee_angle: float,
	wrist_y: float,
	shoulder_y: float = 0.5,
	elbow_y: float = 0.5,
) -> Dict[str, Any]:
	"""
	Create a mock pose result for testing.
	
	Args:
		hip_y: Hip Y coordinate (0-1, lower = higher)
		knee_angle: Knee flexion angle in degrees
		wrist_y: Wrist Y coordinate (0-1, lower = higher)
		shoulder_y: Shoulder Y coordinate
		elbow_y: Elbow Y coordinate
		
	Returns:
		Mock pose result dict
	"""
	# Calculate knee and ankle positions from hip and knee angle
	hip_pos = np.array([0.5, hip_y, 0.0])
	
	# Simple calculation for knee position (below hip)
	knee_pos = np.array([0.5, hip_y + 0.15, 0.0])
	
	# Calculate ankle position based on knee angle
	# Knee angle is between vectors (hip-knee) and (ankle-knee)
	# For simplicity, place ankle directly below knee
	# Adjust distance based on knee angle
	knee_flex_factor = (180 - knee_angle) / 180.0  # 0 = extended, 1 = fully flexed
	ankle_offset = 0.15 * (1 - knee_flex_factor * 0.5)
	ankle_pos = np.array([0.5, knee_pos[1] + ankle_offset, 0.0])
	
	# Arm positions
	shoulder_pos = np.array([0.5, shoulder_y, 0.0])
	elbow_pos = np.array([0.5, elbow_y, 0.0])
	wrist_pos = np.array([0.5, wrist_y, 0.0])
	
	# Create landmarks array (33 points for MediaPipe)
	landmarks = np.zeros((33, 3))
	landmarks[12] = shoulder_pos  # right_shoulder
	landmarks[14] = elbow_pos  # right_elbow
	landmarks[16] = wrist_pos  # right_wrist
	landmarks[24] = hip_pos  # right_hip
	landmarks[26] = knee_pos  # right_knee
	landmarks[28] = ankle_pos  # right_ankle
	
	return {
		"landmarks": landmarks,
		"confidence": np.ones(33) * 0.9,
	}


def create_standard_shot_sequence(num_frames: int = 90) -> List[Dict[str, Any]]:
	"""
	Create a standard jump shot sequence:
	STANCE (0-20) → CROUCH (20-45) → RELEASE (45-60) → LANDING (60-90)
	
	Args:
		num_frames: Total number of frames
		
	Returns:
		List of pose results
	"""
	pose_results = []
	
	for i in range(num_frames):
		if i < 20:
			# STANCE: Upright, knees extended, wrist low
			hip_y = 0.65
			knee_angle = 175
			wrist_y = 0.7
		elif i < 45:
			# CROUCH: Hip descends, knees flex
			progress = (i - 20) / 25.0
			if progress < 0.5:
				# Descending
				hip_y = 0.65 + 0.15 * (progress * 2)
				knee_angle = 175 - 55 * (progress * 2)
			else:
				# Ascending
				ascent = (progress - 0.5) * 2
				hip_y = 0.80 - 0.15 * ascent
				knee_angle = 120 + 55 * ascent
			wrist_y = 0.7 - 0.1 * progress
		elif i < 60:
			# RELEASE: Hip extended, wrist rises
			progress = (i - 45) / 15.0
			hip_y = 0.65
			knee_angle = 175
			wrist_y = 0.6 - 0.4 * progress  # Rising
		else:
			# LANDING: Wrist descends, body returns
			progress = (i - 60) / 30.0
			hip_y = 0.65 + 0.1 * progress
			knee_angle = 175 - 20 * progress  # Slight flex on landing
			wrist_y = 0.2 + 0.3 * progress  # Descending
		
		pose_results.append(create_mock_pose_result(hip_y, knee_angle, wrist_y))
	
	return pose_results


def create_mid_crouch_start_sequence(num_frames: int = 70) -> List[Dict[str, Any]]:
	"""
	Create a sequence that starts mid-crouch (CRITICAL TEST).
	Video begins with person already in crouched position.
	
	CROUCH (0-25) → RELEASE (25-40) → LANDING (40-70)
	
	Args:
		num_frames: Total number of frames
		
	Returns:
		List of pose results
	"""
	pose_results = []
	
	for i in range(num_frames):
		if i < 25:
			# CROUCH: Starts already low, then ascends
			if i < 5:
				# At bottom of crouch
				hip_y = 0.80
				knee_angle = 120
			else:
				# Ascending from crouch
				progress = (i - 5) / 20.0
				hip_y = 0.80 - 0.15 * progress
				knee_angle = 120 + 55 * progress
			wrist_y = 0.6 - 0.1 * (i / 25.0)
		elif i < 40:
			# RELEASE: Wrist rises
			progress = (i - 25) / 15.0
			hip_y = 0.65
			knee_angle = 175
			wrist_y = 0.5 - 0.3 * progress
		else:
			# LANDING: Wrist descends
			progress = (i - 40) / 30.0
			hip_y = 0.65 + 0.1 * progress
			knee_angle = 175 - 20 * progress
			wrist_y = 0.2 + 0.3 * progress
		
		pose_results.append(create_mock_pose_result(hip_y, knee_angle, wrist_y))
	
	return pose_results


def create_quick_release_sequence(num_frames: int = 60) -> List[Dict[str, Any]]:
	"""
	Create a quick release shot (no crouch):
	STANCE (0-30) → RELEASE (30-45) → LANDING (45-60)
	
	Args:
		num_frames: Total number of frames
		
	Returns:
		List of pose results
	"""
	pose_results = []
	
	for i in range(num_frames):
		if i < 30:
			# STANCE: Upright
			hip_y = 0.65
			knee_angle = 175
			wrist_y = 0.7 - 0.1 * (i / 30.0)
		elif i < 45:
			# RELEASE: Direct to release
			progress = (i - 30) / 15.0
			hip_y = 0.65
			knee_angle = 175
			wrist_y = 0.6 - 0.4 * progress
		else:
			# LANDING
			progress = (i - 45) / 15.0
			hip_y = 0.65 + 0.05 * progress
			knee_angle = 175 - 10 * progress
			wrist_y = 0.2 + 0.3 * progress
		
		pose_results.append(create_mock_pose_result(hip_y, knee_angle, wrist_y))
	
	return pose_results


class TestPhaseDetector:
	"""Test suite for PhaseDetector."""
	
	def test_standard_shot(self):
		"""Test detection of standard jump shot."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(90)
		
		phases = detector.detect_phases(pose_results)
		
		# Should detect all 4 phases
		phase_types = [p["phase"] for p in phases]
		assert ShootingPhase.STANCE in phase_types, "Should detect STANCE"
		assert ShootingPhase.CROUCH in phase_types, "Should detect CROUCH"
		assert ShootingPhase.RELEASE in phase_types, "Should detect RELEASE"
		assert ShootingPhase.LANDING in phase_types, "Should detect LANDING"
		
		# Phases should be in order
		phase_names = [p["phase"].value for p in phases]
		expected_order = ["stance", "crouch", "release", "landing"]
		assert phase_names == expected_order, f"Phases out of order: {phase_names}"
		
		# Check temporal consistency (no overlaps)
		for i in range(len(phases) - 1):
			assert phases[i]["end_frame"] < phases[i + 1]["start_frame"], \
				f"Phases {i} and {i+1} overlap"
	
	def test_mid_crouch_start(self):
		"""CRITICAL: Test video starting mid-crouch."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_mid_crouch_start_sequence(70)
		
		phases = detector.detect_phases(pose_results)
		phase_types = [p["phase"] for p in phases]
		
		# Should NOT detect STANCE (video starts in crouch)
		assert ShootingPhase.STANCE not in phase_types, \
			"Should NOT detect STANCE when video starts mid-crouch"
		
		# Should detect CROUCH starting at frame 0
		crouch_phases = [p for p in phases if p["phase"] == ShootingPhase.CROUCH]
		assert len(crouch_phases) > 0, "Should detect CROUCH"
		assert crouch_phases[0]["start_frame"] == 0, \
			"CROUCH should start at frame 0 when video starts mid-crouch"
		
		# Should still detect RELEASE and LANDING
		assert ShootingPhase.RELEASE in phase_types, "Should detect RELEASE"
		assert ShootingPhase.LANDING in phase_types, "Should detect LANDING"
	
	def test_quick_release_no_crouch(self):
		"""Test quick release shot without crouch phase."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_quick_release_sequence(60)
		
		phases = detector.detect_phases(pose_results)
		phase_types = [p["phase"] for p in phases]
		
		# Should detect STANCE and RELEASE, may or may not detect CROUCH
		assert ShootingPhase.STANCE in phase_types, "Should detect STANCE"
		assert ShootingPhase.RELEASE in phase_types, "Should detect RELEASE"
		
		# If CROUCH detected, it should be minimal
		crouch_phases = [p for p in phases if p["phase"] == ShootingPhase.CROUCH]
		if crouch_phases:
			crouch_duration = crouch_phases[0]["end_frame"] - crouch_phases[0]["start_frame"]
			assert crouch_duration < 15, "CROUCH phase should be short or absent in quick release"
	
	def test_initial_state_detection_crouch(self):
		"""Test initial state detection for mid-crouch start."""
		from ..motion_analyzer import analyze_motion_patterns
		
		detector = PhaseDetector(fps=30.0)
		pose_results = create_mid_crouch_start_sequence(70)
		
		# Analyze motion
		motion_signals = analyze_motion_patterns(pose_results, fps=30.0)
		
		# Detect initial state
		initial_state = detector._detect_initial_state(motion_signals)
		
		# Should detect IN_CROUCH or IN_CROUCH_ASCENT
		assert initial_state in [InitialState.IN_CROUCH, InitialState.IN_CROUCH_ASCENT], \
			f"Should detect crouch state, got {initial_state}"
	
	def test_initial_state_detection_stance(self):
		"""Test initial state detection for normal start."""
		from ..motion_analyzer import analyze_motion_patterns
		
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(90)
		
		# Analyze motion
		motion_signals = analyze_motion_patterns(pose_results, fps=30.0)
		
		# Detect initial state
		initial_state = detector._detect_initial_state(motion_signals)
		
		# Should detect IN_STANCE
		assert initial_state == InitialState.IN_STANCE, \
			f"Should detect stance state, got {initial_state}"
	
	def test_get_phase_for_each_frame(self):
		"""Test frame-by-frame phase mapping."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(90)
		
		frame_phases = detector.get_phase_for_each_frame(pose_results)
		
		# Should have phase for every frame
		assert len(frame_phases) == 90, "Should have phase for each frame"
		
		# No frame should be UNKNOWN (all frames covered)
		unknown_count = sum(1 for p in frame_phases if p == ShootingPhase.UNKNOWN)
		assert unknown_count == 0, f"Should not have UNKNOWN phases, got {unknown_count}"
	
	def test_phase_confidence_scores(self):
		"""Test that confidence scores are reasonable."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(90)
		
		phases = detector.detect_phases(pose_results)
		
		for phase in phases:
			confidence = phase["confidence"]
			assert 0.0 <= confidence <= 1.0, \
				f"Confidence {confidence} out of range [0, 1]"
			assert confidence >= 0.5, \
				f"Confidence {confidence} too low for {phase['phase']}"
	
	def test_temporal_consistency(self):
		"""Test that phases don't overlap and are in order."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(90)
		
		phases = detector.detect_phases(pose_results)
		
		# Sort by start frame
		sorted_phases = sorted(phases, key=lambda p: p["start_frame"])
		
		# Check no overlaps
		for i in range(len(sorted_phases) - 1):
			assert sorted_phases[i]["end_frame"] < sorted_phases[i + 1]["start_frame"], \
				f"Phases {i} and {i+1} overlap"
		
		# Check minimum duration
		for phase in phases:
			duration = phase["end_frame"] - phase["start_frame"]
			assert duration >= 1, f"Phase {phase['phase']} too short: {duration} frames"
	
	def test_empty_pose_results(self):
		"""Test handling of empty pose results."""
		detector = PhaseDetector(fps=30.0)
		pose_results = []
		
		phases = detector.detect_phases(pose_results)
		
		assert phases == [], "Should return empty list for empty input"
	
	def test_short_video(self):
		"""Test handling of very short videos."""
		detector = PhaseDetector(fps=30.0)
		pose_results = create_standard_shot_sequence(10)  # Only 10 frames
		
		phases = detector.detect_phases(pose_results)
		
		# Should still return some phases, even if limited
		assert len(phases) >= 1, "Should detect at least one phase"


if __name__ == "__main__":
	# Run tests
	pytest.main([__file__, "-v"])

