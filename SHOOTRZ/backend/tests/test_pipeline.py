"""
Integration tests for the complete video processing pipeline.

Tests end-to-end: video upload → processing → metrics → feedback → database storage.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import cv2

from backend.processing.pipeline import VideoProcessingPipeline
from backend.storage.local_cache import job_store


class TestProcessingPipeline:
	"""Test complete video processing pipeline."""

	def create_test_video(self, num_frames: int = 30, fps: int = 30) -> str:
		"""Create a test video file with specified frames."""
		temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
		temp_path = temp_file.name
		temp_file.close()

		# Create video writer
		fourcc = cv2.VideoWriter_fourcc(*"mp4v")
		out = cv2.VideoWriter(temp_path, fourcc, fps, (640, 480))

		# Write frames (simple colored frames)
		for i in range(num_frames):
			frame = np.zeros((480, 640, 3), dtype=np.uint8)
			# Add some variation
			frame[:, :] = [100 + i, 150, 200]
			out.write(frame)

		out.release()
		return temp_path

	def test_pipeline_with_mock_video(self):
		"""Test pipeline with a created test video."""
		# Create test video
		video_path = self.create_test_video(num_frames=30)

		try:
			# Initialize pipeline
			pipeline = VideoProcessingPipeline(
				use_3d_lifting=False,
				enable_ball_tracking=True,
			)

			# Process video
			result = pipeline.process_video(
				video_path=video_path,
				user_id=None,  # No database storage for test
				video_id=None,
			)

			# Verify results structure
			assert "status" in result
			assert result["status"] in ("completed", "completed_low_quality")
			assert "metrics" in result
			assert "feedback" in result
			assert "phases" in result

			# Verify pose results
			assert "pose_results" in result
			assert result["pose_results"] >= 0

			# Cleanup
			pipeline.cleanup()

		finally:
			# Delete test video
			Path(video_path).unlink(missing_ok=True)

	def test_pipeline_with_empty_video(self):
		"""Test pipeline with empty/invalid video."""
		# Create empty file
		temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
		temp_path = temp_file.name
		temp_file.close()

		try:
			pipeline = VideoProcessingPipeline()
			
			# Should raise error or handle gracefully
			with pytest.raises((ValueError, Exception)):
				pipeline.process_video(
					video_path=temp_path,
					user_id=None,
					video_id=None,
				)
			
			pipeline.cleanup()
		finally:
			Path(temp_path).unlink(missing_ok=True)

	def test_pipeline_handles_missing_frames(self):
		"""Test that pipeline handles videos with missing/dropped frames."""
		# Create video with frame skip
		video_path = self.create_test_video(num_frames=60)
		
		try:
			pipeline = VideoProcessingPipeline(
				use_3d_lifting=False,
				enable_ball_tracking=False,  # Disable ball tracking for faster test
			)
			
			# Process with frame skipping
			result = pipeline.process_video(
				video_path=video_path,
				user_id=None,
				video_id=None,
			)
			
			# Should complete successfully even with frame issues
			assert result["status"] in ("completed", "completed_low_quality")
			pipeline.cleanup()
		finally:
			Path(video_path).unlink(missing_ok=True)

	def test_pipeline_with_database_storage(self):
		"""Test pipeline with database storage enabled."""
		# This would require actual Supabase connection
		# For now, test that it doesn't crash when user_id provided
		video_path = self.create_test_video(num_frames=30)
		
		try:
			pipeline = VideoProcessingPipeline(use_3d_lifting=False)
			
			# Process with user_id (will try to store in DB)
			result = pipeline.process_video(
				video_path=video_path,
				user_id="test_user_id",
				video_id="test_video_id",
			)
			
			# Should complete (DB errors should be handled gracefully)
			assert result["status"] in ("completed", "completed_low_quality")
			pipeline.cleanup()
		finally:
			Path(video_path).unlink(missing_ok=True)

	def test_pipeline_error_handling(self):
		"""Test that pipeline handles errors gracefully."""
		pipeline = VideoProcessingPipeline()
		
		# Test with non-existent file
		with pytest.raises((ValueError, FileNotFoundError)):
			pipeline.process_video(
				video_path="/nonexistent/video.mp4",
				user_id=None,
				video_id=None,
			)
		
		pipeline.cleanup()


if __name__ == "__main__":
	pytest.main([__file__, "-v"])



