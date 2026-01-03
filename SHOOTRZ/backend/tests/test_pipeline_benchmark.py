"""
Benchmark test suite for video processing pipeline.

Tests pipeline on curated test set from UCF Sports and DeepSport,
compares results against ground truth, and validates performance metrics.
"""

import unittest
import json
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.processing.pipeline import VideoProcessingPipeline


class TestPipelineBenchmark(unittest.TestCase):
	"""Benchmark tests for video processing pipeline."""
	
	@classmethod
	def setUpClass(cls):
		"""Set up test class with benchmark data."""
		cls.benchmark_dir = project_root / "data" / "benchmark"
		cls.test_videos_dir = cls.benchmark_dir / "test_videos"
		cls.ground_truth_path = cls.benchmark_dir / "ground_truth.json"
		
		# Load ground truth if available
		cls.ground_truth = {}
		if cls.ground_truth_path.exists():
			with open(cls.ground_truth_path, 'r') as f:
				cls.ground_truth = json.load(f)
	
	def setUp(self):
		"""Set up test instance."""
		self.pipeline = VideoProcessingPipeline(
			use_3d_lifting=False,
			enable_ball_tracking=True,
		)
	
	def tearDown(self):
		"""Clean up after test."""
		self.pipeline.cleanup()
	
	def test_pipeline_completes(self):
		"""Test that pipeline completes without errors."""
		if not self.test_videos_dir.exists():
			self.skipTest("Test videos directory does not exist")
		
		# Find test videos
		video_files = list(self.test_videos_dir.glob("*.mp4")) + \
		              list(self.test_videos_dir.glob("*.avi"))
		
		if not video_files:
			self.skipTest("No test videos found")
		
		# Test on first video
		video_path = video_files[0]
		
		try:
			result = self.pipeline.process_video(
				video_path=str(video_path),
				user_id=None,
				video_id=None,
			)
			
			# Assert pipeline completed
			self.assertEqual(result['status'], 'completed')
			self.assertGreater(result.get('pose_results', 0), 0)
		except Exception as e:
			self.fail(f"Pipeline failed: {e}")
	
	def test_pose_detection_rate(self):
		"""Test that pose detection rate meets minimum threshold."""
		if not self.test_videos_dir.exists():
			self.skipTest("Test videos directory does not exist")
		
		video_files = list(self.test_videos_dir.glob("*.mp4")) + \
		              list(self.test_videos_dir.glob("*.avi"))
		
		if not video_files:
			self.skipTest("No test videos found")
		
		min_detection_rate = 0.8  # 80% of frames should have pose detection
		
		for video_path in video_files[:3]:  # Test first 3 videos
			try:
				result = self.pipeline.process_video(
					video_path=str(video_path),
					user_id=None,
					video_id=None,
				)
				
				# Calculate detection rate (simplified)
				pose_results = result.get('pose_results', 0)
				# Assume ~30fps for 10 second video = 300 frames
				# This is a rough estimate
				estimated_frames = 300
				detection_rate = pose_results / estimated_frames if estimated_frames > 0 else 0
				
				self.assertGreaterEqual(
					detection_rate,
					min_detection_rate,
					f"Pose detection rate {detection_rate:.2%} below threshold {min_detection_rate:.2%}"
				)
			except Exception as e:
				self.fail(f"Test failed on {video_path.name}: {e}")
	
	def test_metrics_generated(self):
		"""Test that metrics are generated for processed videos."""
		if not self.test_videos_dir.exists():
			self.skipTest("Test videos directory does not exist")
		
		video_files = list(self.test_videos_dir.glob("*.mp4")) + \
		              list(self.test_videos_dir.glob("*.avi"))
		
		if not video_files:
			self.skipTest("No test videos found")
		
		video_path = video_files[0]
		
		try:
			result = self.pipeline.process_video(
				video_path=str(video_path),
				user_id=None,
				video_id=None,
			)
			
			metrics = result.get('metrics', [])
			self.assertGreater(len(metrics), 0, "No metrics generated")
			
			# Check for key metrics
			metric_names = [m.get('metric_name') for m in metrics]
			expected_metrics = ['elbow_angle', 'knee_angle', 'release_angle']
			
			for expected in expected_metrics:
				self.assertIn(
					expected,
					metric_names,
					f"Expected metric '{expected}' not found"
				)
		except Exception as e:
			self.fail(f"Test failed: {e}")
	
	def test_ball_tracking_enabled(self):
		"""Test that ball tracking works when enabled."""
		if not self.test_videos_dir.exists():
			self.skipTest("Test videos directory does not exist")
		
		video_files = list(self.test_videos_dir.glob("*.mp4")) + \
		              list(self.test_videos_dir.glob("*.avi"))
		
		if not video_files:
			self.skipTest("No test videos found")
		
		video_path = video_files[0]
		
		try:
			result = self.pipeline.process_video(
				video_path=str(video_path),
				user_id=None,
				video_id=None,
			)
			
			# Ball tracking may or may not detect ball (depends on video)
			# Just check that the field exists
			self.assertIn('ball_trajectory_length', result)
		except Exception as e:
			self.fail(f"Test failed: {e}")
	
	def test_compare_with_ground_truth(self):
		"""Compare pipeline results with ground truth (if available)."""
		if not self.ground_truth:
			self.skipTest("Ground truth not available")
		
		if not self.test_videos_dir.exists():
			self.skipTest("Test videos directory does not exist")
		
		video_files = list(self.test_videos_dir.glob("*.mp4")) + \
		              list(self.test_videos_dir.glob("*.avi"))
		
		if not video_files:
			self.skipTest("No test videos found")
		
		# Find video with ground truth
		for video_path in video_files:
			video_name = video_path.name
			if video_name in self.ground_truth:
				gt_data = self.ground_truth[video_name]
				
				try:
					result = self.pipeline.process_video(
						video_path=str(video_path),
						user_id=None,
						video_id=None,
					)
					
					# Compare metrics (simplified - would need more sophisticated comparison)
					metrics = result.get('metrics', [])
					
					if 'expected_metrics' in gt_data:
						expected = gt_data['expected_metrics']
						for metric_name, expected_value in expected.items():
							# Find corresponding metric in results
							found_metric = next(
								(m for m in metrics if m.get('metric_name') == metric_name),
								None
							)
							
							if found_metric:
								actual_value = found_metric.get('value')
								# Allow 10% tolerance
								tolerance = abs(expected_value * 0.1)
								self.assertAlmostEqual(
									actual_value,
									expected_value,
									delta=tolerance,
									msg=f"Metric {metric_name} mismatch: expected {expected_value}, got {actual_value}"
								)
				except Exception as e:
					self.fail(f"Comparison failed for {video_name}: {e}")
				
				break  # Test on first video with ground truth


if __name__ == "__main__":
	unittest.main()

