"""
Integration test for complete MVP pipeline.

Tests full pipeline from video to report on sample data.
"""

import pytest
import numpy as np
import tempfile
import cv2
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.pipeline import MVPPipeline


class TestIntegration:
    """Integration tests for MVP pipeline."""
    
    def test_pipeline_creates_all_outputs(self, tmp_path):
        """Test that pipeline creates all expected output files."""
        # Create a simple test video
        video_path = tmp_path / "test_shot.mp4"
        self._create_test_video(video_path)
        
        # Run pipeline
        pipeline = MVPPipeline()
        result = pipeline.process_video(str(video_path), shooting_side="right")
        
        # Check that result has expected fields
        assert "run_id" in result
        assert "status" in result
        assert result["status"] == "completed"
        assert "overall_score" in result
        assert "metrics" in result
        assert len(result["metrics"]) == 3  # Three core metrics
        
        # Check that output directory exists
        output_dir = Path(result["output_dir"])
        assert output_dir.exists()
        
        # Check that all expected files exist
        expected_files = [
            "config_used.yaml",
            "video_metadata.json",
            "frame_mapping.csv",
            "pose_keypoints.csv",
            "pose_keypoints.json",
            "pose_keypoints_smoothed.csv",
            "angles.csv",
            "shot_window.json",
            "confidence_summary.json",
            "report.json",
            "run_metadata.json"
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file not found: {filename}"
    
    def _create_test_video(self, video_path: Path, duration: float = 2.0, fps: int = 30):
        """Create a simple test video with moving shapes."""
        width, height = 640, 480
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        
        num_frames = int(duration * fps)
        
        for i in range(num_frames):
            # Create frame with simple animation
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Draw a person-like shape (stick figure)
            # Head
            cv2.circle(frame, (width // 2, height // 4), 30, (255, 255, 255), -1)
            
            # Body
            cv2.line(frame, (width // 2, height // 4 + 30), (width // 2, height // 2), (255, 255, 255), 3)
            
            # Arms (moving)
            arm_y = height // 3 + int(20 * np.sin(i * 0.2))
            cv2.line(frame, (width // 2, height // 3), (width // 2 + 50, arm_y), (255, 255, 255), 3)
            cv2.line(frame, (width // 2, height // 3), (width // 2 - 50, arm_y), (255, 255, 255), 3)
            
            # Legs
            cv2.line(frame, (width // 2, height // 2), (width // 2 + 30, height * 3 // 4), (255, 255, 255), 3)
            cv2.line(frame, (width // 2, height // 2), (width // 2 - 30, height * 3 // 4), (255, 255, 255), 3)
            
            out.write(frame)
        
        out.release()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


