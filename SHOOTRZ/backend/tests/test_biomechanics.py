"""
Unit tests for biomechanics calculations.

Tests angle computations with known inputs and edge cases.
"""

import pytest
import numpy as np
from backend.metrics.biomechanics import (
	joint_angle,
	compute_forearm_verticality,
	compute_elbow_flexion,
	compute_knee_flexion,
	compute_release_angle,
	compute_entry_angle,
)


class TestJointAngle:
	"""Test joint angle computation."""

	def test_right_angle(self):
		"""Test 90-degree angle (perpendicular vectors)."""
		# Right angle triangle
		point_a = np.array([1.0, 0.0, 0.0])  # Shoulder
		point_b = np.array([0.0, 0.0, 0.0])  # Elbow (joint)
		point_c = np.array([0.0, 1.0, 0.0])  # Wrist

		angle = joint_angle(point_a, point_b, point_c)
		assert abs(angle - 90.0) < 0.1, f"Expected 90°, got {angle}°"

	def test_straight_line(self):
		"""Test 180-degree angle (straight line)."""
		point_a = np.array([-1.0, 0.0, 0.0])
		point_b = np.array([0.0, 0.0, 0.0])
		point_c = np.array([1.0, 0.0, 0.0])

		angle = joint_angle(point_a, point_b, point_c)
		assert abs(angle - 180.0) < 0.1, f"Expected 180°, got {angle}°"

	def test_zero_length_vector(self):
		"""Test edge case with zero-length vector."""
		point_a = np.array([0.0, 0.0, 0.0])
		point_b = np.array([0.0, 0.0, 0.0])
		point_c = np.array([1.0, 0.0, 0.0])

		angle = joint_angle(point_a, point_b, point_c)
		assert angle == 0.0, "Zero-length vector should return 0°"


class TestForearmVerticality:
	"""Test forearm verticality computation."""

	def test_perfectly_vertical(self):
		"""Test perfectly vertical forearm."""
		elbow = np.array([0.0, 0.5, 0.0])
		wrist = np.array([0.0, 1.0, 0.0])  # Directly above elbow

		result = compute_forearm_verticality(elbow, wrist)
		assert result["angle_degrees"] < 1.0, "Perfectly vertical should be ~0°"
		assert result["confidence"] == 1.0

	def test_horizontal_forearm(self):
		"""Test horizontal forearm."""
		elbow = np.array([0.0, 0.5, 0.0])
		wrist = np.array([1.0, 0.5, 0.0])  # To the right

		result = compute_forearm_verticality(elbow, wrist)
		assert abs(result["angle_degrees"] - 90.0) < 1.0, "Horizontal should be ~90°"


class TestElbowFlexion:
	"""Test elbow flexion computation."""

	def test_flexed_elbow(self):
		"""Test typical flexed elbow (~80°)."""
		shoulder = np.array([0.0, 1.0, 0.0])
		elbow = np.array([0.0, 0.5, 0.0])
		wrist = np.array([0.3, 0.6, 0.0])  # Bent at ~80°

		result = compute_elbow_flexion(shoulder, elbow, wrist)
		assert 70 <= result["angle_degrees"] <= 90, f"Expected 70-90°, got {result['angle_degrees']}°"
		assert result["confidence"] == 1.0

	def test_extended_elbow(self):
		"""Test extended elbow (~170°)."""
		shoulder = np.array([0.0, 1.0, 0.0])
		elbow = np.array([0.0, 0.5, 0.0])
		wrist = np.array([0.0, 0.0, 0.0])  # Extended

		result = compute_elbow_flexion(shoulder, elbow, wrist)
		assert result["angle_degrees"] > 160, f"Expected >160°, got {result['angle_degrees']}°"


class TestKneeFlexion:
	"""Test knee flexion computation."""

	def test_bent_knee(self):
		"""Test typical crouch position (~108°)."""
		hip = np.array([0.0, 1.0, 0.0])
		knee = np.array([0.0, 0.5, 0.0])
		ankle = np.array([0.2, 0.3, 0.0])  # Bent

		result = compute_knee_flexion(hip, knee, ankle)
		assert 100 <= result["angle_degrees"] <= 120, f"Expected 100-120°, got {result['angle_degrees']}°"


class TestReleaseAngle:
	"""Test ball release angle computation."""

	def test_high_arc_release(self):
		"""Test high-arc release (~75°)."""
		# Ball going up and forward
		trajectory = np.array([
			[0.0, 1.0, 0.0],  # Release point
			[0.5, 2.0, 0.0],  # High and forward
		])

		result = compute_release_angle(trajectory, shot_distance=3.0)
		assert 60 <= result["angle_degrees"] <= 85, f"Expected 60-85°, got {result['angle_degrees']}°"

	def test_low_arc_release(self):
		"""Test low-arc release (~55°)."""
		trajectory = np.array([
			[0.0, 1.0, 0.0],
			[1.0, 1.5, 0.0],  # More horizontal
		])

		result = compute_release_angle(trajectory, shot_distance=6.0)
		assert 45 <= result["angle_degrees"] <= 70, f"Expected 45-70°, got {result['angle_degrees']}°"


class TestEntryAngle:
	"""Test ball entry angle computation."""

	def test_steep_entry(self):
		"""Test steep entry (~50°)."""
		trajectory = np.array([
			[0.0, 2.0, 0.0],
			[0.5, 1.5, 0.0],
			[1.0, 1.0, 0.0],  # Entry point (descending)
		])

		result = compute_entry_angle(trajectory)
		assert 40 <= result["angle_degrees"] <= 60, f"Expected 40-60°, got {result['angle_degrees']}°"


if __name__ == "__main__":
	pytest.main([__file__, "-v"])



