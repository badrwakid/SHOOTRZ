"""
Unit tests for shot detection.

Tests phase detection with synthetic signals.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.shot_detection import ShotDetector


class TestShotDetection:
    """Test shot window detection."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            "knee_flexion_threshold": 100.0,
            "wrist_peak_window": 15,
            "pre_frames": 10,
            "post_frames": 20,
        }
        self.detector = ShotDetector(self.config)
    
    def test_detect_crouch_with_clear_minimum(self):
        """Test crouch detection with clear knee minimum."""
        # Create synthetic knee angles with clear minimum at frame 50
        frames = list(range(100))
        knee_angles = [
            90 + abs(50 - i) * 1.5 if 30 <= i <= 70 else 150
            for i in frames
        ]
        
        angles_df = pd.DataFrame({
            "frame_id": frames,
            "timestamp": [i * 0.033 for i in frames],
            "knee_angle": knee_angles,
            "elbow_angle": [150.0] * 100,
            "wrist_angle": [85.0] * 100,
            "confidence_knee": [0.9] * 100,
            "confidence_elbow": [0.9] * 100,
            "confidence_wrist": [0.9] * 100,
        })
        
        # Create dummy pose keypoints
        joints = ["right_wrist"] * 100 + ["left_wrist"] * 100 + ["nose"] * (100 * 33 - 200)
        pose_df = pd.DataFrame({
            "frame_id": frames * 33,  # 33 joints per frame
            "joint": joints,
            "y_norm_smooth": [0.5] * 100 * 33,
            "confidence": [0.9] * 100 * 33,
        })
        
        shot_window = self.detector.detect_shot_window(angles_df, pose_df, "right")
        
        # Crouch should be near frame 50
        assert 45 <= shot_window["crouch_frame"] <= 55, \
            f"Expected crouch near frame 50, got {shot_window['crouch_frame']}"
        
        assert shot_window["confidence_score"] > 0.3, "Should have usable confidence"
    
    def test_shot_window_structure(self):
        """Test that shot window has all required fields."""
        # Create minimal synthetic data
        angles_df = pd.DataFrame({
            "frame_id": list(range(60)),
            "timestamp": [i * 0.033 for i in range(60)],
            "knee_angle": [120.0] * 30 + [90.0] * 5 + [120.0] * 25,
            "elbow_angle": [150.0] * 60,
            "wrist_angle": [85.0] * 60,
            "confidence_knee": [0.9] * 60,
            "confidence_elbow": [0.9] * 60,
            "confidence_wrist": [0.9] * 60,
        })
        
        pose_df = pd.DataFrame({
            "frame_id": list(range(60)) * 33,
            "joint": ["right_wrist"] * 60 + ["other"] * 60 * 32,
            "y_norm_smooth": [0.5 - i * 0.01 if i < 40 else 0.1 for i in range(60)] + [0.5] * 60 * 32,
            "confidence": [0.9] * 60 * 33,
        })
        
        shot_window = self.detector.detect_shot_window(angles_df, pose_df, "right")
        
        # Check required fields
        assert "start_frame" in shot_window
        assert "crouch_frame" in shot_window
        assert "release_frame" in shot_window
        assert "end_frame" in shot_window
        assert "confidence" in shot_window
        assert "method" in shot_window
        
        # Check logical order
        assert shot_window["start_frame"] <= shot_window["crouch_frame"]
        assert shot_window["crouch_frame"] <= shot_window["release_frame"]
        assert shot_window["release_frame"] <= shot_window["end_frame"]
        assert shot_window["method"] in ["fused_temporal", "knee_minimum_wrist_peak"]
        assert 0.0 <= shot_window["confidence_score"] <= 1.0

    def test_reproducible_detection_same_input(self):
        """Detector should return same key frames for same input."""
        frames = list(range(80))
        angles_df = pd.DataFrame({
            "frame_id": frames,
            "timestamp": [i * 0.033 for i in frames],
            "knee_angle": [160.0] * 20 + [145.0] * 10 + [95.0] * 6 + [130.0] * 12 + [165.0] * 32,
            "elbow_angle": [145.0] * 30 + [160.0] * 20 + [170.0] * 30,
            "wrist_angle": [70.0] * 40 + [85.0] * 20 + [95.0] * 20,
            "confidence_knee": [0.9] * 80,
            "confidence_elbow": [0.9] * 80,
            "confidence_wrist": [0.9] * 80,
        })
        wrist_y = [0.68] * 20 + [0.72] * 10 + [0.78] * 6 + [0.55] * 20 + [0.20] * 10 + [0.30] * 14
        pose_df = pd.DataFrame({
            "frame_id": frames,
            "joint": ["right_wrist"] * len(frames),
            "y_norm_smooth": wrist_y,
            "confidence": [0.9] * len(frames),
        })

        first = self.detector.detect_shot_window(angles_df, pose_df, "right")
        second = self.detector.detect_shot_window(angles_df, pose_df, "right")

        assert first["start_frame"] == second["start_frame"]
        assert first["crouch_frame"] == second["crouch_frame"]
        assert first["release_frame"] == second["release_frame"]
        assert first["end_frame"] == second["end_frame"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




