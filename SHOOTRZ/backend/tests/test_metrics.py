"""
Unit tests for metrics calculator.

Tests metric computation orchestration and edge cases.
"""

import pytest
import numpy as np
from backend.metrics.calculator import MetricsCalculator
from backend.inference.phase_detector import ShootingPhase


class TestMetricsCalculator:
	"""Test metrics calculator orchestration."""

	def test_empty_pose_results(self):
		"""Test with no pose results."""
		calculator = MetricsCalculator(use_3d=False)
		metrics = calculator.compute_all_metrics(
			pose_results=[],
			hand_results=None,
			ball_trajectory=None,
		)
		assert len(metrics) == 0, "Empty pose results should yield no metrics"

	def test_basic_pose_metrics(self):
		"""Test basic metrics from pose results."""
		# Mock pose results (2D landmarks)
		pose_results = [
			{
				"frame_idx": 0,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),  # All landmarks at center
				"confidence": np.ones(33),
				"timestamp_ms": 0.0,
			},
			{
				"frame_idx": 1,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),
				"confidence": np.ones(33),
				"timestamp_ms": 33.33,
			},
		]

		calculator = MetricsCalculator(use_3d=False)
		metrics = calculator.compute_all_metrics(
			pose_results=pose_results,
			hand_results=None,
			ball_trajectory=None,
		)

		# With valid pose data, should compute some metrics
		# (even if values are not realistic)
		assert isinstance(metrics, list), "Should return list of metrics"

	def test_ball_trajectory_metrics(self):
		"""Test metrics from ball trajectory."""
		ball_trajectory = [
			np.array([0.0, 1.0, 0.0]),  # Release
			np.array([0.5, 1.5, 0.0]),
			np.array([1.0, 2.0, 0.0]),  # Apex
			np.array([1.5, 1.5, 0.0]),
			np.array([2.0, 1.0, 0.0]),  # Entry
		]

		calculator = MetricsCalculator(use_3d=False)
		
		# Need minimal pose results for calculator to work
		pose_results = [
			{
				"frame_idx": 0,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),
				"confidence": np.ones(33),
				"timestamp_ms": 0.0,
			},
		]

		metrics = calculator.compute_all_metrics(
			pose_results=pose_results,
			ball_trajectory=ball_trajectory,
		)

		# Should compute trajectory-based metrics
		metric_names = [m["metric_name"] for m in metrics]
		assert "release_angle" in metric_names or "entry_angle" in metric_names, \
			"Should compute trajectory metrics"

	def test_phase_specific_metrics(self):
		"""Test that metrics are computed for specific phases."""
		pose_results = [
			{
				"frame_idx": 0,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),
				"confidence": np.ones(33),
				"timestamp_ms": 0.0,
			},
			{
				"frame_idx": 10,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),
				"confidence": np.ones(33),
				"timestamp_ms": 333.33,
			},
		]

		calculator = MetricsCalculator(use_3d=False)
		metrics = calculator.compute_all_metrics(pose_results=pose_results)

		# Check that phase labels are included where applicable
		for metric in metrics:
			if "phase" in metric:
				assert metric["phase"] in ["stance", "crouch", "release", "landing", "unknown"], \
					f"Invalid phase: {metric['phase']}"

	def test_confidence_scores(self):
		"""Test that confidence scores are included."""
		pose_results = [
			{
				"frame_idx": 0,
				"landmarks": np.array([[0.5, 0.5, 0.0]] * 33),
				"confidence": np.ones(33) * 0.9,  # High confidence
				"timestamp_ms": 0.0,
			},
		]

		calculator = MetricsCalculator(use_3d=False)
		metrics = calculator.compute_all_metrics(pose_results=pose_results)

		# All metrics should have confidence scores
		for metric in metrics:
			assert "confidence" in metric, "Metric should include confidence"
			assert 0.0 <= metric["confidence"] <= 1.0, \
				f"Confidence should be 0-1, got {metric['confidence']}"


if __name__ == "__main__":
	pytest.main([__file__, "-v"])



