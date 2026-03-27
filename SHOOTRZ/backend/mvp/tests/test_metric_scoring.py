"""
Unit tests for metric scoring and verdict assignment.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.metrics import MetricsDerivation


class TestMetricScoring:
    """Test verdict assignment logic."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            "metrics": {
                "elbow_extension": {
                    "good_range": [150, 175],
                    "optimal_range": [160, 170],
                    "release_window": 3
                },
                "knee_bend": {
                    "good_range": [85, 120],
                    "optimal_range": [95, 110]
                },
                "wrist_follow_through": {
                    "good_range": [10, 30],
                    "optimal_range": [15, 25]
                }
            },
            "scoring": {
                "weights": {"elbow": 0.40, "knee": 0.30, "wrist": 0.30},
                "confidence_penalty": 0.5,
                "low_confidence_threshold": 0.4
            }
        }
        self.derivation = MetricsDerivation(self.config)
    
    def test_verdict_good_in_optimal_range(self):
        """Test that optimal values get 'Good' verdict."""
        verdict = self.derivation._assign_verdict(
            value=165.0,  # In optimal range [160, 170]
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Good"
    
    def test_verdict_good_in_good_range(self):
        """Test that good range values get 'Good' verdict."""
        verdict = self.derivation._assign_verdict(
            value=155.0,  # In good range but not optimal
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Good"
    
    def test_verdict_needs_work_outside_range(self):
        """Test that values outside range get 'Needs Work'."""
        verdict = self.derivation._assign_verdict(
            value=140.0,  # Outside good range
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Needs Work"
    
    def test_verdict_low_confidence(self):
        """Test that low confidence returns 'Low Confidence'."""
        verdict = self.derivation._assign_verdict(
            value=165.0,
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.2  # Below threshold
        )
        assert verdict == "Low Confidence"
    
    def test_score_range(self):
        """Test that overall score is in [0, 100] range."""
        # Create synthetic angles data
        angles_df = pd.DataFrame({
            "frame_id": list(range(60)),
            "timestamp": [i * 0.033 for i in range(60)],
            "knee_angle": [100.0] * 60,
            "elbow_angle": [165.0] * 60,
            "wrist_angle": [85.0] * 60,
            "confidence_knee": [0.9] * 60,
            "confidence_elbow": [0.9] * 60,
            "confidence_wrist": [0.9] * 60,
        })
        
        shot_window = {
            "start_frame": 10,
            "crouch_frame": 30,
            "release_frame": 40,
            "end_frame": 50
        }
        
        metrics = self.derivation.derive_metrics(angles_df, shot_window)
        score, feedback = self.derivation.compute_overall_score(metrics)
        
        assert 0 <= score <= 100, f"Score {score} outside [0, 100] range"
    
    def test_good_form_high_score(self):
        """Test that good form produces high score."""
        angles_df = pd.DataFrame({
            "frame_id": list(range(60)),
            "timestamp": [i * 0.033 for i in range(60)],
            "knee_angle": [105.0] * 60,  # Optimal
            "elbow_angle": [165.0] * 60,  # Optimal
            "wrist_angle": [80.0] * 30 + [100.0] * 30,  # 20 degree change
            "confidence_knee": [0.95] * 60,
            "confidence_elbow": [0.95] * 60,
            "confidence_wrist": [0.95] * 60,
        })
        
        shot_window = {
            "start_frame": 10,
            "crouch_frame": 30,
            "release_frame": 40,
            "end_frame": 50
        }
        
        metrics = self.derivation.derive_metrics(angles_df, shot_window)
        score, feedback = self.derivation.compute_overall_score(metrics)
        
        # All optimal should give high score
        assert score >= 80, f"Expected score >= 80 for optimal form, got {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




