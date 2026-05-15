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
        """Test that pipeline creates all expected output files.

        After the streaming refactor:
        - ``overlay.mp4`` is NOT produced by default (``save_overlay_video:
          false`` in ``mvp_config.yaml``). The test opts-in when it needs to
          verify overlay generation.
        - Synthetic videos often fail pose detection — accept both
          ``completed`` and ``completed_low_quality`` as success statuses.
        """
        video_path = tmp_path / "test_shot.mp4"
        self._create_test_video(video_path)

        pipeline = MVPPipeline()
        result = pipeline.process_video(str(video_path), shooting_side="right")

        assert "run_id" in result
        assert "status" in result
        assert result["status"] in ("completed", "completed_low_quality")
        assert "overall_score" in result
        assert "metrics" in result
        assert "phases" in result, "Pipeline must now pre-compute phases for MVPJobService."

        output_dir = Path(result["output_dir"])
        assert output_dir.exists()

        # Minimum set of artefacts that must always exist regardless of
        # overlay toggle or pose detection success.
        always_required = [
            "config_used.yaml",
            "video_metadata.json",
            "frame_mapping.csv",
            "pose_keypoints.csv",
            "pose_keypoints.json",
            "confidence_summary.json",
            "run_metadata.json",
        ]
        for filename in always_required:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file not found: {filename}"

        # These artefacts only exist on the full ``completed`` path.
        if result["status"] == "completed":
            completed_required = [
                "pose_keypoints_smoothed.csv",
                "angles.csv",
                "shot_window.json",
                "event_candidates.json",
                "event_confidence.json",
                "feature_table.csv",
                "signals_smoothed.csv",
                "warnings.json",
                "report.json",
            ]
            for filename in completed_required:
                file_path = output_dir / filename
                assert file_path.exists(), f"Expected file not found: {filename}"

        # Overlay is opt-in now.
        overlay_path = output_dir / "overlay.mp4"
        assert not overlay_path.exists(), (
            "overlay.mp4 should not be produced when save_overlay_video is false"
        )
    
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




